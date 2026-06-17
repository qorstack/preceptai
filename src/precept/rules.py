"""Repo-local, user-editable cognition rules — `agents/preceptai/<domain>/rules.md`.

Built-in packs (`precept.packs.builtin`) ship as code; this module lets ordinary
users override or extend them per repo by editing plain Markdown. `quickstart`
seeds one file per built-in domain so there's always a starting point to edit,
and the files live in the user's repo (committed, shared via git).
"""

from __future__ import annotations

from pathlib import Path

from precept.packs.builtin import BUILTIN_PACKS, get_pack
from precept.packs.schema import CognitionPack

# (attribute on CognitionPack, human heading)
_SECTIONS = [
    ("business_rules", "Business rules"),
    ("common_requirements", "Common requirements"),
    ("risk_flags", "Risk flags"),
    ("required_workflow", "Required workflow"),
    ("forbidden_shortcuts", "Forbidden shortcuts"),
    ("questions_to_ask", "Questions to ask"),
]


def rules_dir(repo_path: str | Path = ".") -> Path:
    return Path(repo_path) / "agents" / "preceptai"


def rules_file(repo_path: str | Path, domain: str) -> Path:
    # One rules.md per domain inside the OKF tree: agents/preceptai/<domain>/rules.md
    return rules_dir(repo_path) / domain.lower() / "rules.md"


def pack_to_markdown(pack: CognitionPack) -> str:
    """Render a built-in pack as editable Markdown."""
    lines = [f"# {pack.domain} rules", ""]
    if getattr(pack, "description", ""):
        lines += [pack.description, ""]
    for attr, title in _SECTIONS:
        items = getattr(pack, attr, None) or []
        if not items:
            continue
        lines.append(f"## {title}")
        lines += [f"- {item}" for item in items]
        lines.append("")
    related = getattr(pack, "related_domains", None) or []
    if related:
        lines += ["## Related domains", ", ".join(related), ""]
    lines += [
        "<!-- Edit these rules freely. They're surfaced to the AI for this domain,",
        "     overriding the built-in defaults. Committed to the repo so the team",
        "     shares them. -->",
        "",
    ]
    return "\n".join(lines)


def load_repo_rules(repo_path: str | Path, domain: str) -> str | None:
    """Return the repo-local rules Markdown for a domain, or None if not present."""
    path = rules_file(repo_path, domain)
    if not path.exists():
        return None
    try:
        return path.read_text(encoding="utf-8").strip() or None
    except OSError:
        return None


def rules_for_domain(repo_path: str | Path, domain: str) -> str | None:
    """Repo-local rules if the team edited them, else the built-in pack as Markdown."""
    local = load_repo_rules(repo_path, domain)
    if local:
        return local
    pack = get_pack(domain)
    return pack_to_markdown(pack) if pack else None


def scaffold_rules(repo_path: str | Path) -> list[str]:
    """Write one editable `.md` per built-in domain. Never clobbers existing files."""
    rules_dir(repo_path).mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    for domain, pack in BUILTIN_PACKS.items():
        path = rules_file(repo_path, domain)
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(pack_to_markdown(pack), encoding="utf-8")
            written.append(domain)
    return written
