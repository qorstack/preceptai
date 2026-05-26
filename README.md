# knowai

**Cognitive enforcement layer for AI software development.**

> Knowledge is passive. Cognition must be enforced.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

---

## What it does

AI assistants generate code fast but don't understand your system — they duplicate utilities, miss conventions, and re-invent decisions.

knowai sits between Claude / Cursor and your repo. Via MCP, it returns:

```text
Domain:    payment (HIGH)
Decision:  WARN — follow team conventions
Reuse:     PaymentClient, IdempotencyMiddleware
Memory:    "Use idempotency keys" (alice, approved)
Risk:      refund → webhook → ledger
```

Storage: **Postgres** with semantic auto-merge. Web dashboard for the team.

Every entry has two axes so it's clear where it applies and who wrote it:

| Scope ↓ / Source → | 👤 Human (added in dashboard) | 🤖 AI (saved by Claude via MCP) |
| --- | --- | --- |
| 🌐 **Global** — every workspace | Team-wide policies | _(rare)_ |
| 📁 **Workspace** — one project | Project decisions | Auto-tagged from `knowai.config` |

AI-written entries land as **Pending** until a human reviews them on the dashboard.

---

## Prerequisites

- Docker + Docker Compose v2
- Python 3.11+ with `uv` (only for Part 2)
- ~2GB free RAM

---

## Part 1 — Dashboard

### 1. Create `.env`

```env
POSTGRES_USER=knowai
POSTGRES_PASSWORD=knowai
POSTGRES_DB=knowai
POSTGRES_PORT=5432
WEB_PORT=8080
```

### 2. Create `docker-compose.yml`

```yaml
services:
  postgres:
    image: pgvector/pgvector:pg16
    container_name: knowai-postgres
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    ports: ["${POSTGRES_PORT}:5432"]
    volumes: [knowai_pgdata:/var/lib/postgresql/data]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $$POSTGRES_USER"]
      interval: 5s

  web:
    image: qorstack/knowai:latest
    container_name: knowai-web
    depends_on: { postgres: { condition: service_healthy } }
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_HOST: postgres
      POSTGRES_PORT: 5432
    ports: ["${WEB_PORT}:8080"]

volumes:
  knowai_pgdata:
```

### 3. Start & open

```bash
docker compose up -d
open http://localhost:8080
```

Use the dashboard to add knowledge entries by hand. Done — or continue to Part 2 for AI integration.

---

## Part 2 — AI integration

### 4. Install the CLI

```bash
uv tool install git+https://github.com/qorstack/knowai.git
knowai --version
```

### 5. Create `knowai.config` at each repo root

```toml
workspace = "my-product"
repo_name = "aaa-api"

[database]
host     = "localhost"
port     = 5432
user     = "knowai"
password = "knowai"
db       = "knowai"
schema   = "public"
```

> Or put `[database]` in `~/.knowai.config` once and per-repo files only need `workspace` + `repo_name`.

When Claude saves memory via MCP, knowai auto-tags it with `scope=workspace`, this `workspace`, and this `repo_name` — entries land in the right bucket on the dashboard without any extra work.

### 6. Register knowai with Claude Code

```bash
claude mcp add --scope user knowai -- knowai mcp
claude mcp list   # should show: knowai ✓
```

### 7. Install the slash commands

```bash
knowai install-claude-commands     # copies /knowai and /knowai-generate to ~/.claude/commands/
```

Two commands ship:

| Command | Use it when |
| --- | --- |
| `/knowai <request>` | **Every feature / refactor / fix.** Forces Claude to run the full pipeline (analyze_intent → recall_context → get_reusable_assets → assess_risk_in_context) and open with a `Risk:` / `Decision:` header before writing code. |
| `/knowai-generate` | **Once, then occasionally.** Have Claude read this repo and seed meaningful memory entries. Safe to re-run after refactors. |

> Why a slash command? MCP tool descriptions only reach Claude when it _decides_ to use a tool — a plain prompt can slip past the pipeline. `/knowai` makes the consult mandatory.

### 8. Verify

In Claude, try:

```text
/knowai add a refund endpoint to /payments
```

You should see a reply that opens with `Risk: <level> — <why>` / `Decision: ...` and references your stored memory in the `Memory:` line.

If not: `claude mcp list` shows `✗` → run `knowai mcp` in a terminal to see the error (usually missing DB credentials).

---

## Dashboard at a glance

- **Home** — two hero cards: ⏳ **Pending review** (AI entries awaiting approval) + 🌐 **Global knowledge**. Plus a per-workspace breakdown.
- **Knowledge** — workspace pills at the top, then filter by source (Human / AI), status (Approved / Pending), or domain. Every row shows scope + source badges.
- **Entry detail** — full metadata strip plus a **Move to Global ↑** / **Move to Workspace ↓** button so you can re-scope without re-creating.
- **Summaries / Activity** — per-domain AI syntheses and full audit log.

---

## CLI cheat sheet

```bash
knowai memory list                                # all entries
knowai memory recall "OTP policy"                 # fuzzy search
knowai memory decide payment "Use idempotency" --body "..."
knowai memory forget <entry-id>
```

Dashboard URLs: `/entries` · `/syntheses` · `/audit` · `/healthz`

---

## Stop / wipe

```bash
docker compose stop                # keep data
docker compose down -v             # wipe all data
docker compose pull web && docker compose up -d   # upgrade
```

---

## Troubleshooting

| Problem                                        | Fix                                                                                                    |
| ---------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| `docker compose up` fails                      | Docker Desktop not running                                                                             |
| `knowai: command not found`                    | Open a new terminal (uv PATH not loaded)                                                               |
| AI doesn't call knowai tools                   | `knowai.config` missing or AI app started before MCP registered — restart it                           |
| AI entries land as Global instead of Workspace | Repo has no `knowai.config`, or it's missing `workspace`. Run `knowai link <workspace> --name <repo>`  |
| Upgraded CLI but MCP still old                 | Restart Claude Code — it caches the MCP subprocess until restart                                       |
| Two entries not merging                        | Bodies <0.92 cosine similarity. Reword closer, or check `docker compose logs web` for embedding errors |
| Port already in use                            | Change `POSTGRES_PORT` / `WEB_PORT` in `.env`                                                          |

---

## Build from source

```bash
git clone https://github.com/qorstack/knowai.git && cd knowai
cp .env.example .env
docker compose up -d --build
uv sync --extra dev --extra postgres
uv run pytest
```

---

MIT — see [LICENSE](LICENSE).
