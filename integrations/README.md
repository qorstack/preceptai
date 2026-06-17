# Sage integrations — one protocol, every agent

The protocol lives in **[`../AGENTS.md`](../AGENTS.md)** (single source of truth).
This folder mirrors what goes in your repo root — copy only what your tool needs.

## Usage

```bash
# Claude Code
cp -r integrations/.claude .

# Cursor
cp -r integrations/.cursor .

# Windsurf
cp -r integrations/.windsurf .

# Cline
cp -r integrations/.clinerules .

# GitHub Copilot
cp -r integrations/.github .

# Gemini CLI
cp integrations/GEMINI.md .
```

## What gets placed

| Copy | Destination | For |
| --- | --- | --- |
| `.claude/` | `.claude/commands/` | Claude Code |
| `.cursor/` | `.cursor/rules/sage.mdc` | Cursor |
| `.windsurf/` | `.windsurf/rules/sage.md` | Windsurf |
| `.clinerules/` | `.clinerules/sage.md` | Cline |
| `.github/` | `.github/instructions/sage*.instructions.md` | GitHub Copilot |
| `GEMINI.md` | `GEMINI.md` | Gemini CLI |

**OpenAI Codex, OpenCode, Google Antigravity** read `AGENTS.md` natively —
no adapter needed, just keep `AGENTS.md` at your repo root.

Each adapter is intentionally tiny: "read and follow `AGENTS.md`." Edit the
protocol in one place and every agent stays in step.

> Don't see your agent? Most modern agents support either `AGENTS.md` or a
> rules/instructions file — point it at `AGENTS.md` the same way.
