"""
Per-repo link config — precept.config at the root of each project repo.

The same file may also carry a [database] section (read by precept/__init__.py).
Link fields live at the top level; DB credentials nest under [database].

Schema:
    workspace = "my-product"     # required — name of the workspace
    repo_name = "api"            # optional — overrides folder name
    role = "backend"             # optional — backend|frontend|worker|...
    domains = ["billing", "auth"]  # optional — declared domains
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from precept.paths import repo_link_config_path


class LinkConfig(BaseModel):
    workspace: str
    repo_name: str = ""
    role: str = "unknown"
    domains: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    critical: bool = False
    knowledge_remote: str = ""
    """Git remote URL of the shared workspace (knowledge) repo.

    When set, this is the canonical address devs should clone into
    ~/.precept/workspaces/<workspace>/. Precept surfaces this URL in
    error messages when the local workspace folder is missing, so
    no one has to hunt for "where is the shared knowledge?".
    """
    auto_approve_ai_memory: bool = False
    """If true, AI-written business_context memory is approved at save time
    instead of landing as Pending. Humans curate by editing/forgetting on the
    dashboard rather than approving each new entry. Per-repo override of the
    same key in ~/.precept.config."""
    metadata: dict[str, Any] = Field(default_factory=dict)

    def resolved_repo_name(self, repo_path: str | Path) -> str:
        return self.repo_name or Path(repo_path).resolve().name


def load_global_link() -> dict | None:
    """Read top-level workspace identity from ~/.precept.config.

    Returns a dict with workspace/role/domains/tags if the file declares a
    `workspace` key at the top level. Used by the resolver as a fallback so
    every repo auto-joins the user's default workspace without needing its
    own precept.config.
    """
    path = Path.home() / ".precept.config"
    if not path.exists():
        return None
    try:
        import tomllib
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if "workspace" not in data:
        return None
    return {
        "workspace": str(data["workspace"]),
        "role":      str(data.get("role", "unknown")),
        "domains":   list(data.get("domains", [])),
        "tags":      list(data.get("tags", [])),
        "auto_approve_ai_memory": bool(data.get("auto_approve_ai_memory", False)),
    }


def load_link(repo_path: str | Path = ".") -> LinkConfig | None:
    """Return LinkConfig if precept.config exists and declares workspace, else None."""
    path = repo_link_config_path(repo_path)
    if not path.exists():
        return None
    try:
        import tomllib  # py3.11+
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except ImportError:
        try:
            import tomli as tomllib  # type: ignore
            data = tomllib.loads(path.read_bytes())
        except ImportError:
            data = _simple_toml_parse(path.read_text(encoding="utf-8"))
    if "workspace" not in data:
        return None
    return LinkConfig(
        workspace=str(data["workspace"]),
        repo_name=str(data.get("repo_name", "")),
        role=str(data.get("role", "unknown")),
        domains=list(data.get("domains", [])),
        tags=list(data.get("tags", [])),
        critical=bool(data.get("critical", False)),
        knowledge_remote=str(data.get("knowledge_remote", "")),
        auto_approve_ai_memory=bool(data.get("auto_approve_ai_memory", False)),
        metadata=dict(data.get("metadata", {})),
    )


def save_link(config: LinkConfig, repo_path: str | Path = ".") -> Path:
    """Write precept.config inside repo_path, preserving any [database] section."""
    path = repo_link_config_path(repo_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    db_section = _extract_database_section(path)
    text = _serialize(config)
    if db_section:
        text = text.rstrip() + "\n\n" + db_section
    path.write_text(text, encoding="utf-8")
    return path


def _extract_database_section(path: Path) -> str:
    """Return the [database] section of an existing file, including the heading."""
    if not path.exists():
        return ""
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return ""
    lines = text.splitlines()
    start = next((i for i, ln in enumerate(lines) if ln.strip() == "[database]"), -1)
    if start < 0:
        return ""
    end = len(lines)
    for j in range(start + 1, len(lines)):
        s = lines[j].strip()
        if s.startswith("[") and s.endswith("]") and s != "[database]":
            end = j
            break
    return "\n".join(lines[start:end]).rstrip() + "\n"


def _serialize(config: LinkConfig) -> str:
    lines = [
        f'workspace = "{config.workspace}"',
    ]
    if config.knowledge_remote:
        lines.append(f'knowledge_remote = "{config.knowledge_remote}"')
    if config.repo_name:
        lines.append(f'repo_name = "{config.repo_name}"')
    if config.role and config.role != "unknown":
        lines.append(f'role = "{config.role}"')
    if config.domains:
        lines.append(f"domains = {_toml_list(config.domains)}")
    if config.tags:
        lines.append(f"tags = {_toml_list(config.tags)}")
    if config.critical:
        lines.append("critical = true")
    if config.auto_approve_ai_memory:
        lines.append("auto_approve_ai_memory = true")
    lines.append("")
    return "\n".join(lines)


def _toml_list(values: list[str]) -> str:
    inner = ", ".join(f'"{v}"' for v in values)
    return f"[{inner}]"


def _simple_toml_parse(text: str) -> dict[str, Any]:
    """Minimal TOML parser for top-level key/value (no tomllib/tomli fallback)."""
    result: dict[str, Any] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("["):
            continue
        if "=" not in line:
            continue
        k, _, v = line.partition("=")
        k = k.strip()
        v = v.strip()
        if v.startswith("[") and v.endswith("]"):
            inner = v[1:-1].strip()
            result[k] = [item.strip().strip('"').strip("'") for item in inner.split(",") if item.strip()]
        elif v in ("true", "false"):
            result[k] = (v == "true")
        else:
            result[k] = v.strip('"').strip("'")
    return result
