# Sage

This project uses **Sage**. Before writing or modifying any code, read and
follow **`AGENTS.md`** at the repo root — the cognition protocol.

Every code change runs five steps. Steps 1–3 before code; steps 4–5 after.

---

**Model & effort ceiling — applies to every step.** Read the actual model and
effort from the current session context before starting — never assume from
memory or a previous run. State what you detected in the intent block.

- **Ceiling = the session effort, and it is also the default.** You may go
  BELOW it for trivial sub-tasks, but NEVER above it — for any reason. If the
  session is `@ low`, **every** task is `low`, even complex ones. "Standard
  implementation" or "complex logic" is not a reason to raise above the session
  level — the ceiling always wins.
- **Floor:** default `sonnet @ low`. Use `haiku @ low` for trivial
  fully-specified tasks with no decisions (translation/rewording, adding a log
  line, an explicit one-line edit) to save tokens — `sonnet` for anything
  touching logic or behavior
- **Effort levels** (meaning only, not a target): `low` · `medium` · `high` ·
  `max` — ignore any level above the session effort
- **Format:** state full version + effort for every task (≤ session) —
  e.g. `sonnet 4.6 @ effort:low`

---

**Before code:**

1. Pick the role lens (`architect`, `dev`, `debugger`, `frontend`, `qa`, …) —
   infer from the request. Roles hand off between phases.
   **Open `agents/sage/roles/role-<lens>.md` immediately.**
   - Found → read it, adopt as-is, output: `Role: <lens> [loaded]`
   - Missing → write the file to disk now, output: `Role: <lens> [created]`
   On handoff output: `Role: <new-lens> [loaded] — handoff from <prev-lens>`.
   Never start a phase without outputting the role line.
2. Read `agents/sage/<domain>/rules.md` and relevant `decisions/` files.
   Quote the rules that apply. Find reusable assets — **open the source file
   and read its exports** before using them. Never infer an API from a name.
   **Multi-repo workspace:** anchor all paths to the repo root of the file
   being edited. Add `Repo: <repo-root>` to the intent block. Never read or
   write knowledge across repos.
3. Output the intent block, then declare a **parallel plan**:

   ```text
   Role    : <role> — <task>
   Model   : <version> @ effort:<level>  ← detected from session, not memory
   Intent  : <what this change does>
   Touches : <files, systems, domains>
   Risk    : LOW | MEDIUM | HIGH — <why>
   Decision: proceed | warn | ask | reject
   ```

   Group plan tasks by phase (`[parallel]` or `[sequential]`). Annotate each
   task with its tier. Mark tasks with 🟨 when starting, ✅ when done,
   ❌ on failure (pause immediately — never continue silently).

**After code:**

1. Capture knowledge — mandatory, every run. Write to `agents/sage/` in the
   repo, never to local memory. Write the pattern, not the implementation.
   `[new]` create a `decisions/<slug>.md` · `[updated]` fix stale entry ·
   `[none]` name the existing rule that covered this.
2. **A response without this block is incomplete.** Output as plain markdown:

   *Debugger / bug fix:*

   ```markdown
   ── Sage ──────────────────────────────────────────
   **Role** · debugger — <task>
   **Model** · <version> @ effort:<level>
   **Domain** · <domain> | **Risk** · <LOW|MEDIUM|HIGH>

   **Root cause**
   <why it broke — name the exact function/variable/condition>

   **Mechanism**
   - <trigger>
   - <propagation>
   - <symptom>

   **Fix**
   - <what changed and why it addresses the root cause>
   - <trade-offs, if any>

   **Validated**
   <concrete evidence — not "looks correct">

   **Slipped**
   <why it wasn't caught>

   **Knowledge** · [new | updated | none] `<path>` — <reason>
   ──────────────────────────────────────────────────
   ```

   *Dev / build task:*

   ```markdown
   ── Sage ──────────────────────────────────────────
   **Role** · <role> — <task>
   **Model** · <version> @ effort:<level>
   **Domain** · <domain> | **Risk** · <LOW|MEDIUM|HIGH>

   **Done**
   <what was built or changed>

   **Decisions**
   - <key choice and why>
   - <alternatives considered and ruled out>

   **Validated**
   <how you confirmed it works>

   **Knowledge** · [new | updated | none] `<path>` — <reason>
   ──────────────────────────────────────────────────
   ```

`AGENTS.md` is the source of truth — follow it verbatim.
