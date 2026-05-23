"""
Auto-sync helpers — keep the knowledge repo in sync with git without
asking the human to type `git pull` / `git push`.

Design goals:
- **Never lose data.** All writes happen locally first, then we attempt to
  push. If the network is down, the local change is still there.
- **Never block.** All git ops have short timeouts. Failures are logged and
  surfaced but never raise — auditing happens at the call site.
- **Opt-out friendly.** Set `KNOWLYX_AUTO_SYNC=0` to disable globally.
- **Silent on success.** Devs shouldn't see git noise when things work.

Public API:
    sync_enabled()         — is auto-sync turned on for this process?
    pull(workspace_dir)    — git pull --rebase --autostash, returns SyncResult
    push(workspace_dir,    — git add+commit+push, retries once on non-FF.
         files, message)
    full_sync(workspace_dir, message, files=...)
                           — pull → push. Used by `knowlyx sync`.

All helpers no-op (gracefully) when:
- the workspace folder isn't a git repo
- the repo has no `origin` remote
- KNOWLYX_AUTO_SYNC=0
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

DEFAULT_TIMEOUT = 15  # seconds — short enough to avoid hangs


@dataclass
class SyncResult:
    ok: bool
    action: str  # "pull" | "push" | "skip"
    detail: str = ""
    skipped_reason: str = ""


def sync_enabled() -> bool:
    """Honor KNOWLYX_AUTO_SYNC env var. Default: enabled."""
    val = os.environ.get("KNOWLYX_AUTO_SYNC", "1").strip().lower()
    return val not in ("0", "false", "no", "off")


def _is_git_repo(path: Path) -> bool:
    return (path / ".git").exists() or _git(path, ["rev-parse", "--is-inside-work-tree"]).returncode == 0


def _has_remote(path: Path, remote: str = "origin") -> bool:
    r = _git(path, ["remote", "get-url", remote])
    return r.returncode == 0 and bool(r.stdout.strip())


def _git(cwd: Path, args: list[str], timeout: int = DEFAULT_TIMEOUT) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        # Synthesize a failure result so callers don't need to handle exceptions.
        return subprocess.CompletedProcess(args=args, returncode=1, stdout="", stderr=str(e))


def _skip(reason: str) -> SyncResult:
    return SyncResult(ok=True, action="skip", skipped_reason=reason)


def _preflight(workspace_dir: str | Path) -> tuple[Path, SyncResult | None]:
    """Common checks. Returns (path, skip_result) — if skip_result is not None, bail."""
    if not sync_enabled():
        return Path(workspace_dir), _skip("KNOWLYX_AUTO_SYNC=0")
    p = Path(workspace_dir).expanduser().resolve()
    if not p.exists():
        return p, _skip(f"path does not exist: {p}")
    if not _is_git_repo(p):
        return p, _skip("not a git repo")
    if not _has_remote(p):
        return p, _skip("no `origin` remote")
    return p, None


# ------------------------------------------------------------------
# Pull
# ------------------------------------------------------------------


def pull(workspace_dir: str | Path) -> SyncResult:
    """
    `git pull --rebase --autostash` — quietly bring local up to date with origin.

    Returns SyncResult.ok = False if rebase needs human intervention (conflict).
    The local working tree is left in the rebase-in-progress state so the user
    can resolve and continue.
    """
    p, skip = _preflight(workspace_dir)
    if skip is not None:
        return skip
    r = _git(p, ["pull", "--rebase", "--autostash", "origin"])
    if r.returncode == 0:
        return SyncResult(ok=True, action="pull", detail=(r.stdout or "").strip())
    # If rebase failed mid-way, abort it so the working tree is clean.
    in_rebase = (p / ".git" / "rebase-merge").exists() or (p / ".git" / "rebase-apply").exists()
    if in_rebase:
        _git(p, ["rebase", "--abort"], timeout=5)
    return SyncResult(
        ok=False,
        action="pull",
        detail=(r.stderr or r.stdout or "").strip(),
    )


# ------------------------------------------------------------------
# Push
# ------------------------------------------------------------------


def push(
    workspace_dir: str | Path,
    files: list[str] | None,
    message: str,
) -> SyncResult:
    """
    Stage `files` (or all changes if files is None), commit, and push to origin.

    Retries once with a pull-rebase + push on non-fast-forward rejection.
    Returns SyncResult.ok=True if push succeeded, .ok=False otherwise (local
    commit still exists; caller can surface "needs manual push").
    """
    p, skip = _preflight(workspace_dir)
    if skip is not None:
        return skip

    # Stage
    if files:
        add_args = ["add", "--", *files]
    else:
        add_args = ["add", "-A"]
    add = _git(p, add_args)
    if add.returncode != 0:
        return SyncResult(ok=False, action="push", detail=f"git add failed: {add.stderr.strip()}")

    # Anything to commit?
    status = _git(p, ["status", "--porcelain"])
    if not status.stdout.strip():
        # No changes — but check if there are unpushed commits we should push.
        unpushed = _git(p, ["log", "@{u}..HEAD", "--oneline"])
        if not unpushed.stdout.strip():
            return SyncResult(ok=True, action="push", detail="nothing to push")
    else:
        commit = _git(p, ["commit", "-m", message])
        if commit.returncode != 0:
            return SyncResult(ok=False, action="push", detail=f"git commit failed: {commit.stderr.strip()}")

    # Push, with one auto-retry on non-fast-forward.
    for attempt in range(2):
        pushed = _git(p, ["push", "origin", "HEAD"])
        if pushed.returncode == 0:
            return SyncResult(ok=True, action="push", detail="pushed")
        out = (pushed.stderr or "").lower()
        if attempt == 0 and ("non-fast-forward" in out or "rejected" in out or "fetch first" in out):
            # remote moved — rebase on top and try again
            rebase = pull(p)
            if not rebase.ok:
                return SyncResult(ok=False, action="push", detail=f"rebase failed during push retry: {rebase.detail}")
            continue
        return SyncResult(ok=False, action="push", detail=(pushed.stderr or pushed.stdout or "").strip())

    return SyncResult(ok=False, action="push", detail="push failed after retry")


# ------------------------------------------------------------------
# Composite
# ------------------------------------------------------------------


def full_sync(
    workspace_dir: str | Path,
    message: str = "",
    files: list[str] | None = None,
) -> tuple[SyncResult, SyncResult]:
    """
    Pull then push. Returns (pull_result, push_result).

    Used by both the `knowlyx sync` CLI command and the post-write hooks in
    `knowlyx memory decide`, `knowlyx approval ...`, and `knowlyx init`.
    """
    pr = pull(workspace_dir)
    if not pr.ok and pr.action != "skip":
        # If pull failed (conflict), don't try to push — surface the conflict.
        return pr, SyncResult(ok=False, action="push", detail="skipped: pull failed first")
    msg = message or "chore(knowlyx): auto-sync"
    push_result = push(workspace_dir, files, msg)
    return pr, push_result
