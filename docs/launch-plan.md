# Precept — launch plan

Goal: make Precept genuinely production-usable and clearly stronger than
autonomous agents like Hermes **in the lane they don't play in** — governance
and enforcement — then ship a Product Hunt launch that converts.

Guiding rule: don't fight Hermes at "smartest autonomous agent." Win at
"the layer a team trusts before an agent touches prod." Precept rides on top of
any agent over MCP.

Status legend: ✅ done · 🔜 next · ⬜ later · 🌐 external (needs your accounts)

---

## Phase A — Make the claim true (credibility)

The README says "AI cannot skip it." Today that's still soft (prompt-level).
Close that gap.

1. ✅ **Hard enforcement** — `precept check` (exit 2 = reject · 1 = ask/strict),
   the existing `precept commit-check` pre-commit hook, and a GitHub Action
   (`cognition-gate.yml`) that fails any PR the engine would reject. Can't be
   skipped with `--no-verify`. _Next: analyze the actual diff, not just the PR
   intent text._
2. ⬜ **Decision logging** — persist every `analyze_intent` verdict (decision,
   risk, domain) so the dashboard can show real "blocked / paused" history,
   not just memory edits.
3. ⬜ **Secret safety** — guarantee memory never stores secrets (extend the
   existing sanitization; add a test corpus).

## Phase B — Prove "works with any agent"

Hermes sells "runs anywhere." Precept must answer.

4. ⬜ **Multi-agent quickstart** — documented + tested setup for Cursor and
   Copilot (MCP), not just Claude Code. One table: agent → install command.
5. ⬜ **Reliable auto-capture** — capture team decisions from commit messages /
   PR descriptions, not only when the agent remembers to call `remember_*`.

## Phase C — Retention + proof (why teams keep it)

6. ⬜ **Impact/value metrics** — dashboard tiles: "risky changes blocked",
   "assets reused", "decisions enforced this week". This is both retention and
   Product Hunt proof.
7. 🔜 **Dashboard home = decisions feed** — lead with recent STOP/ASK moments
   and pending review (cards), not a raw table.
8. ⬜ **Interactive impact graph** — render the existing `export_graph`
   (react_flow) on screen; domain × risk you can click.

## Phase D — Go to market (the launch surface)

9. ✅ **Interactive playground** (`/playground`) — repo-less, real engine,
   now renders a real markdown reply.
10. ⬜ **Landing page (static)** — hero + demo GIF + install + GitHub star.
    Host on Vercel / GitHub Pages, separate from the dashboard.
11. ⬜ **Hosted playground** — deploy the `/playground` route as a tiny public
    service (Fly/Render); no DB needed, so anyone can try it from the landing.
12. ✅ **Demo media** — real GIF + screenshots in `assets/demo/`.
13. 🌐 **Publish** — PyPI `precept-ai`, GitHub repo rename, ghcr image, so
    `uv tool install precept-ai` and `precept quickstart` work for everyone.
14. 🌐 **Product Hunt** — copy, first-20 supporters, launch Tue–Thu 00:01 PST,
    founder answering comments all day.

---

## Already shipped (this rebrand round)

- ✅ Rename knowai → Precept (CLI `precept` + `prc`, dist `precept-ai`)
- ✅ Plain-language positioning + differentiation table in README
- ✅ `precept quickstart` (one command) + `precept web` (local dashboard)
- ✅ Bulk-approve + no-name approve in the dashboard
- ✅ Smarter file-store recall (token + partial + trigram)
- ✅ Interactive playground with real markdown response
- ✅ Real demo GIF / screenshots

## Suggested order

Phase A (1 → 2) first — it's the credibility moat vs Hermes. Then D-10/11
(landing + hosted playground) for the launch, then C-6 (metrics) for retention.

## The two surfaces, to be explicit

- **Public** (marketing): landing page + hosted playground — fast, shareable,
  no DB. This is what Product Hunt clicks.
- **Private** (product): the self-hosted dashboard (`precept web` / docker) —
  holds each team's memory, approvals, and audit.
