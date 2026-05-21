# Knowlyx

**Cognitive enforcement layer for AI software development.**

AI coding tools write code fast — but they don't understand your system.  
Knowlyx forces AI to understand business logic, architecture, and impact *before* touching code.

## One-line install (Claude Code)

```bash
claude mcp add knowlyx -- uvx knowlyx mcp --repo .
```

That's it. Claude Code will now call Knowlyx tools before generating any code.

## What it does

When you ask Claude to *"fix payment scan 501"*, Knowlyx intercepts and tells Claude:

```
Domain:   payment (CRITICAL)
Action:   fix
Impact:   webhook-service, worker, audit-service, notification-service
Cascade:  payment → webhook (retry risk), payment → audit (log required)
Decision: WARN — follow required workflow before proceeding

Workflow:
  1. Update backend DTO
  2. Regenerate Swagger spec
  3. Rebuild generated client
  4. Run integration tests
```

Claude cannot skip this. It's enforced at the tool level.

## CLI

```bash
uvx knowlyx scan /path/to/repo
uvx knowlyx analyze "add OTP login" --repo /path/to/repo
uvx knowlyx impact "fix payment scan 501" --repo /path/to/repo
uvx knowlyx conventions /path/to/repo
uvx knowlyx assets payment --repo /path/to/repo
```

## MCP Tools (what Claude calls)

| Tool | Purpose |
| --- | --- |
| `analyze_intent` | Full cognitive report — call this first, always |
| `get_conventions` | Rules AI must follow in this repo |
| `get_reusable_assets` | Existing components/hooks/utils to reuse |
| `get_impact_analysis` | Blast radius of a planned change |
| `get_risk_analysis` | Risk level + proceed/warn/ask/reject decision |
| `get_project_context` | Lightweight session orientation |
| `remember_business_context` | Save approved business understanding |
| `recall_context` | Fuzzy search memory for relevant context |
| `approve_convention` | Human approves a convention as canonical |

## Self-host

```bash
git clone https://github.com/knowlyx/knowlyx
cd knowlyx
uv sync
uv run knowlyx mcp --repo /path/to/your/project
```

## Optional: Vector memory (Qdrant)

For semantic fuzzy memory across sessions:

```bash
docker run -p 6333:6333 qdrant/qdrant
uv sync --extra vector
```

Knowlyx detects Qdrant automatically. Falls back to JSON file storage when unavailable.

## Architecture

```
Scanner → Cognitive Graph → Reasoning Engine → MCP Server → Claude
              ↓
         Memory Layer (file / Qdrant)
              ↓
         Cognition Packs (domain knowledge bundles)
```

## License

MIT
