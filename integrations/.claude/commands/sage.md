# /sage — Sage cognition pipeline

Run before any non-trivial code change. Steps 1–3 run **before** you write code.
Steps 4–5 run **after**. All five are mandatory — never skip, never abbreviate.

---

## Step 1 — Pick your role

Name the domain + action. Pick the lens the task actually calls for — not just
`dev`. Any senior expert applies: `frontend`, `infra`, `security`, `qa`,
`architect`, `designer`, `data`, `writer` … infer it yourself.

Look for `agents/sage/roles/role-<lens>.md`:

- Found → adopt it as-is. Update it if this task reveals something new the role owns.
- Missing → create it (Ikigai format: Loves / Good at / Team needs / Worth it + How I work).

State it first: `Role: frontend — building ecommerce landing`

---

## Step 2 — Read knowledge + find assets

1. Open `agents/sage/<domain>/rules.md` and any `decisions/` files whose title
   looks relevant. **Quote the rules that apply** — show the human you checked.
   If the domain folder is missing, note it and continue.

2. Search for reusable assets (utils, hooks, components, services). When you
   find one: **open the source file and read its exports**. Never infer an API
   from a name or decision description. Source is always authoritative.

---

## Step 3 — State intent before writing

Output this block, then wait for `ask`/`reject` before continuing:

```text
Role    : <role> — <one-line task summary>
Intent  : <what this change does>
Touches : <files, systems, domains affected>
Risk    : LOW | MEDIUM | HIGH — <why in one phrase>
Decision: proceed | warn | ask | reject

Plan
1. …
2. …
```

---

## [write the code]

---

## Step 4 — Capture knowledge (mandatory, every run)

Knowledge always goes to `agents/sage/` **in the repo** — never to local memory,
never to a scratch file. After writing, record what you learned. Every run must
output exactly one of:

**A — New knowledge.** Create `agents/sage/<domain>/decisions/<slug>.md`.
Write the **pattern**, not the implementation:

- Good: "Team uses CSS custom properties for all color tokens"
- Bad: "ecommerce-landing.md uses `--bg: #0f0f0f`"

Write it so a new team member with no context can apply it next time.
Use this shape: what the pattern is · why · Do / Avoid.
Set `enforcement: advise`, `source: ai`, `status: proposed`.

**B — Updated knowledge.** An existing entry was relevant; note if it was
accurate or stale. Update in place.

**C — No new knowledge.** Existing rules fully covered this.
State it explicitly: `No new knowledge — <file> covers this case.`

One-line entries count. What's not allowed is silence.

---

## Step 5 — Summary (mandatory, every run)

**A response without this block is incomplete.** Output as **plain markdown**
(no code fence) the block that matches your role. Write in **full sentences**
— a field that fits in five words is too abbreviated. Use bullet points for
multi-step content (Mechanism, Fix, Decisions).

**When role = debugger / fixing a bug:**

```markdown
── Sage ──────────────────────────────────────────
**Role** · debugger — <task in one line>
**Domain** · <domain> | **Risk** · <LOW | MEDIUM | HIGH>

**Root cause**
Explain the specific condition, code path, or wrong assumption that caused the
failure. Name the exact function/variable responsible.

**Mechanism**
- <trigger: what initiated the failure>
- <propagation: how it spread to the surface>
- <symptom: what the user or log observed>

**Fix**
- <what changed>
- <why it addresses the root cause>
- <trade-offs or caveats the team should know>

**Validated**
State the concrete evidence you observed — network tab, log output, test result,
manual check. "Looks correct" is not validation.

**Slipped**
Explain why this wasn't caught earlier — missing test, non-obvious API behaviour,
misleading naming, or an assumption that turned out wrong.

**Knowledge** · [new] `<path>` — <pattern title>
──────────────────────────────────────────────────
```

**When role = dev / architect / frontend / any build task:**

```markdown
── Sage ──────────────────────────────────────────
**Role** · <role> — <task in one line>
**Domain** · <domain> | **Risk** · <LOW | MEDIUM | HIGH>

**Done**
Describe what was built or changed — sections, files, and their purpose.

**Decisions**
- <key choice and why>
- <alternatives considered and ruled out>

**Validated**
Describe how you confirmed it works — what you ran, what you checked, what the
output looked like.

**Knowledge** · [new | updated | none] `<path>` — <pattern or reason>
──────────────────────────────────────────────────
```
