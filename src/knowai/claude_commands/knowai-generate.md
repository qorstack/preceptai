---
description: Seed knowai memory with semantically meaningful entries by reading this repo's code and calling knowai MCP tools.
---

You are seeding the **knowai memory store** for this repository. Your job is to produce entries that future AI calls (`get_reusable_assets`, `recall_context`, `analyze_intent`) can actually use — not a structural file dump.

**This command is safe to re-run at any time** — for an initial seed, after a refactor, after adding a new domain, or when a teammate says "the memory feels stale." Always check `recall_context` first so you don't duplicate work, then add / update only what changed.

## Workflow (do these in order)

### 1. Orient

Call `get_project_context` to learn the repo's language, framework, architecture, and detected domains. Use the detected domains as the primary `domain` field for every entry below. Fall back to `general` only when nothing fits.

### 1b. Diff against what's already stored

Before writing anything, call `list_memory` (or `recall_context` per domain) to fetch existing entries for this repo's workspace. For every candidate you'd otherwise create, **compare it to the closest existing entry** and pick one of three actions:

| Existing entry | Candidate matches the code today? | Action |
| --- | --- | --- |
| None similar | — | **Create** (call `remember_*`) |
| Same kind + title, body still accurate | Yes | **Skip** — nothing changed |
| Same kind + title, body is stale (code moved, signature changed, rule evolved) | No | **Update** — call `remember_*` with the same kind + title; the store upserts by `sha256(kind:domain:title)` so the body / tags / metadata get refreshed in place |
| Title drifted (e.g. you'd now name it differently) | — | **Update** the existing entry's body to match reality. Don't create a near-duplicate with a slightly different title |

When in doubt about whether something is "stale," re-read the source file and quote the line that contradicts the stored body in your re-run summary so the human can sanity-check.

### 2. Pull scanner findings

Call `get_reusable_assets` (per detected domain) and `get_conventions` to see what the rule-based scanner spotted. Treat this as a **lead list**, not the final answer — most leads need verification by reading the file.

### 3. Verify before saving

For every asset, convention, or risk you want to persist, **read the relevant file** with the Read tool first. Skip the entry if:

- The file is generated / vendored / a test fixture
- The asset is trivial (single re-export, empty index, `cn` helper that's just `clsx`)
- The "convention" is a default from the framework, not a team choice

### 4. Write meaningful entries

For each entry that survives step 3, call the matching MCP tool. The 6 kinds and when to use them:

| Kind                | When to save                                                                                   |
| ------------------- | ---------------------------------------------------------------------------------------------- |
| `business_context`  | Domain rules from comments/docs/tests (e.g. "OTP expires after 5 min, max 3 retries")          |
| `approved_convention` | Patterns enforced by code or comments (e.g. "All routes use the `requireAuth` middleware")   |
| `team_decision`     | Choices visible in code with no other "right" answer (e.g. "Money stored as cents, not float") |
| `reusable_asset`    | Components / hooks / services worth pointing future AI at — with file path AND a one-line "use this when…" |
| `risk_pattern`      | Things that look fine but break in production (e.g. "Don't call `setState` in `useEffect` without deps array") |
| `workflow`          | Multi-step procedures the team follows (e.g. "Adding a new payment provider: 1. impl Gateway interface 2. register in factory 3. add e2e test") |

Use `remember_business_context` for the first 3 + last 1, `remember_team_decision` when the entry is a *decision* (auto-approved, no human gate), and direct DB inserts via the existing MCP `remember_*` family for the rest.

### 5. Title and body rules

- **Title**: a sentence a teammate would search for. `"PaymentService — Stripe charge wrapper with idempotency"`, not `"service: service"`.
- **Body**: 2-5 sentences. Include: what it does, when to reach for it, the file path. For conventions, include a concrete example.
- **Domain**: lowercase noun matching the project's detected domains. Don't invent new ones unless the code clearly uses a domain word that wasn't detected.
- **Tags**: 2-5 lowercase tokens. Useful for `recall_context` to score relevance.

### 6. Skip the noise

Do NOT save:

- Generic utilities (`cn`, `formatDate`, `sleep`) — every project has these
- Files whose only purpose is re-exporting (`index.ts` barrel files)
- Conventions that are just linter defaults (e.g. "use ESLint" is not a convention worth storing)
- Duplicates — search with `recall_context` first; if a similar entry exists, skip rather than create a near-duplicate

### 7. Report

After you finish, print a summary in this exact shape so the user can scan it fast:

```text
Re-run summary
  Added:    N (kind breakdown)
  Updated:  N (kind breakdown)
  Skipped:  N already-saved · N noise
```

End with one sentence pointing the user at the dashboard's "Pending review" card if any entries went in unapproved.

---

**Why this matters:** the old `knowai generate` CLI was rule-based pattern matching — it produced 40 entries that looked like data but had no semantic value (`service: service` ×10, `util: cn`, etc.). Your job is to do better by actually reading the code.
