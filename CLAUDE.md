# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What Knowlyx Is

Knowlyx is a **cognitive enforcement layer for AI software development** — not an AI coding assistant. Its purpose is to force AI agents to *understand* a software system (business logic, architecture, UX patterns, reusable assets, impact) *before* generating or modifying code.

Core thesis: **Knowledge is passive. Cognition must be enforced.**

## Development Commands

```bash
# Install (requires uv)
uv sync

# Run CLI
uv run knowlyx --help
uv run knowlyx scan /path/to/repo
uv run knowlyx analyze "add OTP login" --repo /path/to/repo
uv run knowlyx impact "fix payment scan 501" --repo /path/to/repo
uv run knowlyx conventions /path/to/repo
uv run knowlyx assets payment --repo /path/to/repo
uv run knowlyx pack payment          # show built-in cognition pack

# Memory commands
uv run knowlyx memory list --repo /path/to/repo
uv run knowlyx memory recall "OTP policy" --repo /path/to/repo
uv run knowlyx memory decide payment "Use idempotency keys" --body "All payment calls require idempotency key" --repo /path/to/repo
uv run knowlyx memory forget <entry-id> --repo /path/to/repo

# Start MCP server (stdio — for Claude Code integration)
uv run knowlyx mcp --repo /path/to/repo

# Start MCP server (SSE — for HTTP clients)
uv run knowlyx mcp --sse --port 8765 --repo /path/to/repo

# Start REST API
uv run uvicorn knowlyx.api.main:app --reload --port 8000

# Run tests
uv run pytest

# Run single test
uv run pytest tests/test_memory.py::test_persistence -v

# Lint
uv run ruff check src/
uv run ruff format src/

# Build for PyPI
uv build
uv publish   # requires PYPI_TOKEN
```

## Architecture

Six layers, each in its own package under `src/knowlyx/`:

| Layer | Package | Responsibility |
| --- | --- | --- |
| Scanner | `scanner/` | Reads repo, infers language/framework/architecture, detects conventions and assets |
| Cognitive Graph | `graph/` | NetworkX DiGraph of domains, assets, conventions, and impact edges |
| Reasoning | `reasoning/` | Intent → Impact → Risk → Decision pipeline (rule-based, no LLM needed) |
| MCP Server | `mcp/` | FastMCP tools that AI agents must call before touching code |
| CLI | `cli/` | Typer CLI wrapping all cognitive commands |
| REST API | `api/` | FastAPI mirror of MCP tools for HTTP clients |

### Core data flow

```text
User request (string)
  → IntentAnalyzer     → IntentAnalysis   (domain, action, inferred requirements)
  → ImpactAnalyzer     → ImpactAnalysis   (affected domains, services, files, cascade risks)
  → RiskScorer         → RiskAssessment   (level, decision: proceed/warn/ask/reject)
  → ReasoningEngine    → CognitionReport  (full report with plan and reusable assets)
```

### MCP Tools (the enforcement surface)

All tools live in `src/knowlyx/mcp/server.py`. AI agents call these via MCP before coding:

#### Phase 1 — Cognitive analysis

- `analyze_intent(request, repo_path)` — **call first**, full CognitionReport + packs + memory
- `get_conventions(repo_path)` — detected rules AI must follow
- `get_reusable_assets(domain, repo_path)` — existing assets to reuse before creating new code
- `get_impact_analysis(change_description, repo_path)` — blast radius of a change
- `get_risk_analysis(request, repo_path)` — risk level + proceed/warn/ask/reject decision
- `get_project_context(repo_path)` — lightweight session orientation
- `get_cognition_pack(domain)` — built-in domain knowledge (auth/otp/payment/webhook/order/notification/worker)
- `refresh_scan(repo_path)` — bust the scan cache

#### Phase 2 — Memory + Human approval

- `remember_business_context(domain, title, body, repo_path)` — save business knowledge (requires approval)
- `approve_memory(entry_id, approved_by, repo_path)` — human approves a memory as trusted
- `recall_context(query, domain, repo_path)` — fuzzy search approved memories
- `remember_team_decision(domain, title, decision, reason, repo_path)` — save + auto-approve team decisions
- `list_memory(domain, repo_path)` — list all memory entries
- `forget_memory(entry_id, repo_path)` — delete a memory entry

### Claude Code MCP configuration

Add to `.claude/settings.json` in any target repo:

```json
{
  "mcpServers": {
    "knowlyx": {
      "command": "uv",
      "args": ["run", "knowlyx", "mcp", "--repo", "."],
      "cwd": "/path/to/knowlyx"
    }
  }
}
```

## Key Design Rules

- **MCP-first, not markdown-first** — Claude ignores markdown files. All cognition is delivered as structured tool results that Claude *must* query.
- **No LLM calls in the reasoning engine** — all reasoning is rule-based. Claude (via MCP) does the higher-level synthesis.
- **Scan cache** — `_state` dict in both `mcp/server.py` and `api/main.py` caches per `repo_path`. Call `refresh_scan` after structural changes.
- **Risk decisions are binding** — `reject` means stop; `ask` means pause for human confirmation. Never auto-proceed past these.
- **Multi-repo aware** — `repo_path` is always explicit; tools can target any repo, not just the one Knowlyx lives in.

### Phase 3 — Workspace + Graph export + Approval queue

- `get_workspace_context(workspace_path)` — full multi-repo overview from knowlyx.toml
- `get_cross_repo_impact(changed_repo, change_description, workspace_path)` — cross-repo blast radius
- `export_graph(format, repo_path, workspace_path)` — react_flow | mermaid | dot
- `request_approval(title, description, risk_level, domain, ...)` — submit approval gate
- `check_approval(request_id)` — poll outcome (pending/approved/rejected)
- `approve_request(request_id)` / `reject_request(request_id, reason)` — human tools
- `list_approvals(status_filter)` — list approval queue

### Workspace (multi-repo)

Defined in `src/knowlyx/workspace/`. Driven by `knowlyx.toml` at workspace root:

```toml
name = "my-product"

[[repos]]
name = "api"
path = "./api"
role = "backend"
domains = ["payment", "auth"]
critical = true

[[repos]]
name = "web"
path = "./web"
role = "frontend"

[[dependencies]]
from = "web"
to = "api"
type = "api"
```

CLI: `knowlyx workspace init | scan | impact <repo> -c "..." | graph [mermaid|dot|react_flow]`

### Graph export

`src/knowlyx/graph/exporter.py` — `GraphExporter` produces:

- **React Flow JSON** — drop-in for `<ReactFlow nodes={} edges={} />` (Phase 3 frontend)
- **Mermaid** — paste into any markdown
- **DOT** — render with Graphviz

### Approval queue

`src/knowlyx/approval/queue.py` — stored in `.knowlyx/approvals.json`.

Flow: AI calls `request_approval()` → stores as `pending` → human runs `knowlyx approval approve <id>` → AI polls `check_approval()` → proceeds only on `approved`.

CLI: `knowlyx approval list | show <id> | approve <id> | reject <id> --reason "..."`

## Planned (Phase 4)

- AI self-review before submitting code
- Risk scoring ML model
- Architectural enforcement hooks
- Design cognition (UX/UI pattern detection)
- Local LLMs via Ollama
