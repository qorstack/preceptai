# Precept

![Precept](assets/logo-full.png)

**Knowledge is passive. Cognition must be enforced.**

Precept is a **cognition protocol** for AI coding agents — a single
[`AGENTS.md`](AGENTS.md) plus a folder of Markdown knowledge. No install, no
server, no Python, no MCP. Any agent that reads `AGENTS.md` (Claude Code,
Cursor, Codex, Copilot, …) is forced to *understand* your system — your team's
rules, the blast radius, what to reuse — **before** it writes code.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## The problem

AI agents write code fast and break prod fast. They reinvent a service the team
already wrote, ignore a rule agreed on six months ago, and ship it. Docs and RAG
are passive — the agent reads them only if it remembers to. Precept makes
consulting the team's knowledge a **required step in the agent's workflow**,
written as plain rules the agent must follow.

## Install — copy one file into your repo

```bash
# 1. drop the protocol at your repo root
curl -fsSL https://raw.githubusercontent.com/qorstack/preceptai/main/AGENTS.md -o AGENTS.md

# 2. (optional) grab the starter knowledge to build on
git clone --depth 1 https://github.com/qorstack/preceptai tmp-precept \
  && cp -r tmp-precept/agents . && rm -rf tmp-precept
```

Commit both and you're done. That's the entire setup — every agent on the team
that reads `AGENTS.md` now follows the protocol. Improve it by editing the file;
share it by pushing.

> No starter knowledge needed to begin: the protocol tells the agent to capture
> rules as you work, so `agents/preceptai/` fills in over time.

## How it works (full protocol in [`AGENTS.md`](AGENTS.md))

- **Pipeline before code** — name the intent, read `agents/preceptai/<domain>/`,
  reuse before creating, assess impact/risk, emit a `Risk:` / `Decision:` header
  (`proceed | warn | ask | reject`), and stop on `ask` / `reject`.
- **Knowledge as Markdown** — `agents/preceptai/<domain>/rules.md` +
  `decisions/<slug>.md`, each with YAML frontmatter (`status`, `enforcement`,
  `applies_to`, …). Human + AI editable, diffable, shared via git.
- **Learns from you** — when you state a rule or correction in chat, the agent
  writes it as a `status: proposed` entry; you approve by flipping it to
  `approved`. Governed, not silent.
- **Enforcement levels** — `block` (refuse violations), `warn` (flag), `advise`
  (strong default).

## Why a single file

| | Docs / RAG / MCP server | Precept (`AGENTS.md`) |
| --- | --- | --- |
| Setup | install + run a service | copy one file |
| Consulted before code | optional / if sampled | required step in the protocol |
| Returns a verdict | facts only | `proceed / warn / ask / reject` |
| Edit a rule | code / DB / UI | edit Markdown, commit |
| Share with the team | deploy / sync | `git push` |
| Works across agents | per-tool integration | every agent reads `AGENTS.md` |

## Edit the rules

They're yours. Open `agents/preceptai/payment/rules.md` (or any domain), change
the rules, commit. The agent follows your team's version. Add a new decision as
a small Markdown file under `agents/preceptai/<domain>/decisions/`.

---

MIT — see [LICENSE](LICENSE). Promo site: [preceptai.qorstack.com](https://preceptai.qorstack.com).
