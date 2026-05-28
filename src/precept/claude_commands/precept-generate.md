---
description: Seed precept memory with semantically meaningful entries by reading this repo's code and calling precept MCP tools.
---

You are seeding the **precept memory store** for this repository. Your job is to produce entries that future AI calls (`get_reusable_assets`, `recall_context`, `analyze_intent`) can actually use — not a structural file dump, but also not a backend-only snapshot.

**Coverage is the success metric.** A typical full-stack repo has 5–10 distinct areas (backend services, frontend pages, design system, build/config, tests, infra). The rule-based scanner only sees ~2 domains; **do not stop where the scanner stops.** You are expected to walk the tree yourself.

**This command is safe to re-run at any time** — for an initial seed, after a refactor, after adding a new area, or when a teammate says "the memory feels stale." Always diff against existing memory first, then add / update only what changed.

## Workflow

### 1. Orient

Call `get_project_context` to learn the repo's language, framework, architecture, and the domains the scanner detected. **These detected domains are a starting point, not the whole map.** Skim the response, but plan to expand it.

### 2. Walk the tree (don't trust the scanner alone)

Use `Glob` and directory reads to enumerate the actual top-level structure under `src/`, `app/`, `apps/*/src/`, `packages/*/src/`, or whatever this project uses. List every folder that looks like a distinct concern (e.g. `src/server/`, `src/views/`, `src/components/`, `src/store/`, `src/admin/`, `prisma/`, `agents/`, `config/`). Build a mental map of areas before you save anything.

If `get_project_context` returned `domains: ["auth"]` but the tree has `src/payment/`, `src/exam/`, `src/notification/` — **trust the tree**, not the scanner.

### 3. Diff against what's already stored

Call `list_memory` (no domain filter) once, then `recall_context` per candidate area, to fetch existing entries for this repo's workspace. For every candidate you'd otherwise create, compare it to the closest existing entry and pick one of three actions:

| Existing entry | Candidate matches the code today? | Action |
| --- | --- | --- |
| None similar | — | **Create** (call `remember_*`) |
| Same kind + title, body still accurate | Yes | **Skip** — nothing changed |
| Same kind + title, body is stale (code moved, signature changed, rule evolved) | No | **Update** — call `remember_*` with the same kind + title; the store upserts by `sha256(kind:domain:title)` so the body / tags / metadata get refreshed in place |
| Title drifted (e.g. you'd now name it differently) | — | **Update** the existing entry's body to match reality. Don't create a near-duplicate with a slightly different title |

When unsure if something is stale, re-read the source and quote the line that contradicts the stored body in your re-run summary.

### 4. Sweep every area — coverage checklist

Walk each of these areas (skip ones that genuinely don't exist in this repo). For each area, read 3–8 representative files and decide what's worth saving. Aim for **2–8 high-signal entries per area**, not one per file.

| Area | What to look for | Likely kinds |
| --- | --- | --- |
| **Backend services / routes** | route handler shape, auth/session, response envelope, error model, validation | `approved_convention`, `team_decision`, `workflow` |
| **Domain logic** (per business domain found in tree) | the rules that make this domain work: invariants, lifecycle, edge cases | `business_context`, `team_decision` |
| **Database / persistence** | schema invariants, ID type, JSON columns, migration patterns, transaction rules | `team_decision`, `approved_convention` |
| **Frontend pages / views** | page composition, layout/provider stack, data-fetching pattern, routing | `approved_convention`, `reusable_asset` |
| **Components / hooks** | non-trivial reusable pieces (skip cn/clsx/index re-exports) | `reusable_asset` |
| **State management** | store shape, slice conventions, server-state vs client-state split | `approved_convention`, `team_decision` |
| **Design system / UX rules** | color tokens, typography stack, spacing scale, "do/don't" rules from team docs (often in `docs/`, `agents/`, `design/`) | `approved_convention`, `team_decision` |
| **Build / config** | non-default Next/Vite config, transpilePackages, polyfills, env-cmd flow, monorepo wiring | `team_decision`, `risk_pattern` |
| **Tests** | test framework, real-DB vs mocks, fixtures pattern, what gets covered vs skipped | `approved_convention`, `workflow` |
| **Infra / deploy** | docker-compose, Dockerfile decisions, CI flow, secrets handling | `team_decision`, `risk_pattern` |
| **Stale / contradictory docs** | README/CLAUDE.md that contradicts code, leftover scaffolding, generated code mistaken for hand-written | `risk_pattern` |

You do NOT need to cover every file in an area — pick the load-bearing ones. But you DO need to touch every area that exists.

### 5. Verify before saving

For every candidate, **read the source file** with the Read tool before calling `remember_*`. Skip the entry if:

- The file is generated / vendored / a test fixture (`src/api/generated/`, `node_modules`, `.next/`)
- The asset is trivial (single re-export, empty index, `cn` helper that's just `clsx`)
- The "convention" is a default from the framework (Next.js file-system routing isn't a team choice)
- A near-duplicate already exists in memory (from step 3)

### 6. Write meaningful entries — the 6 kinds

| Kind | When to save | Saved via |
| --- | --- | --- |
| `business_context` | Domain rules from comments / docs / tests ("OTP expires after 5 min, max 3 retries") | `remember_business_context` (pending) |
| `approved_convention` | Patterns enforced by code or comments ("All routes use the `requireAuth` middleware") | `remember_business_context` (pending) |
| `team_decision` | Explicit choices with no other "right" answer ("Money stored as cents, not float") | `remember_team_decision` (auto-approved) |
| `reusable_asset` | Components / hooks / services worth pointing future AI at — with file path + "use when…" | `remember_business_context` (pending) |
| `risk_pattern` | Things that look fine but break in production ("Don't call `setState` in `useEffect` without deps array") | `remember_business_context` (pending) |
| `workflow` | Multi-step procedures the team follows ("Adding a payment provider: 1. impl Gateway 2. register in factory 3. add e2e test") | `remember_business_context` (pending) |

Default to `remember_business_context` (lands as pending). Use `remember_team_decision` only when the entry is clearly an explicit team choice — these auto-approve, so don't smuggle inferences in.

### 7. Title and body rules

- **Title**: a sentence a teammate would search for. `"PaymentService — Stripe charge wrapper with idempotency"`, not `"service: service"`.
- **Body**: 2–5 sentences. Include: what it does, when to reach for it, the file path. For conventions, include a concrete example.
- **Domain**: lowercase noun. Prefer domains you saw in the tree over the scanner's list. Use `general` only when nothing else fits.
- **Tags**: 2–5 lowercase tokens that `recall_context` can match against.

### 8. Skip the noise

Do NOT save:

- Generic utilities (`cn`, `formatDate`, `sleep`) — every project has these
- Files whose only purpose is re-exporting (`index.ts` barrel files)
- Conventions that are just linter defaults
- Near-duplicates of existing entries

### 9. Report — show coverage

Print this summary in exactly this shape. The **Areas covered** matrix is required — it's how the user knows you didn't stop at backend.

```text
Re-run summary
  Added:    N (kind breakdown, e.g. 5 team_decision · 9 business_context)
  Updated:  N (kind breakdown)
  Skipped:  N already-saved · N noise

Areas covered (read at least one file from each):
  [✓] backend services       N entries
  [✓] domain: <name>         N entries
  [✓] frontend pages         N entries
  [—] design system          (no docs/ or agents/ found)
  [✓] build/config           N entries
  [✓] tests                  N entries
  [✓] stale docs flagged     N entries

Pending review: N entries waiting for human approval at /entries?status=pending
```

If you ran out of context before covering everything, mark the unfinished areas with `[?]` and list what you'd cover on the next re-run. **Honest gaps beat fake completeness.**

---

**Why this matters:** the old `precept generate` CLI produced 40 entries that looked like data but had no semantic value (`service: service` ×10, `util: cn`, etc.). Your job is to do better by actually reading the code — across every area of the project, not just the parts the scanner happened to detect.
