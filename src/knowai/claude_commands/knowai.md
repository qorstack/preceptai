---
description: Run the full knowai cognition pipeline before answering any coding request — surfaces risk, reuses team knowledge, and stops you from inventing solutions the team has already decided against.
---

The user wants you to consult **knowai** before doing anything. Treat the prompt that follows as a coding request and run the full pipeline below. **Do not skip steps. Do not paraphrase steps. Do not assume you already know the answer.**

## Pipeline — execute in order

### 1. `analyze_intent(request)`

Call this first with the user's request verbatim. The response gives you:

- `domain` + risk level
- `decision`: `proceed` | `warn` | `ask` | `reject`
- impacted areas + cascade
- existing approved memory that's relevant

### 2. `recall_context(query, domain)`

Search memory for prior team decisions, conventions, and business rules in this domain. **Quote anything relevant in your reply** — the user needs to see that you actually checked.

### 3. `get_reusable_assets(domain)`

List components / services / utilities the team already has. **Reuse before you create.** If the request maps to an existing asset, point at it instead of writing new code.

### 4. `assess_risk_in_context(request)`

You may UPGRADE the rule-based decision from step 1 if historical context warrants it. You may NEVER downgrade it.

### 5. Open your reply with this header — required

```text
Risk: <LOW | MEDIUM | HIGH> — <one-sentence why>
Decision: <proceed | warn | ask | reject>
Reuse: <names of reusable assets, or "none applicable">
Memory: <1-3 quoted lines from recall_context, or "no relevant entries">
```

Then write the actual response.

### 6. Respect the decision

| Decision | What you do |
| --- | --- |
| `proceed` | Carry out the request. Mention the conventions / assets you're following. |
| `warn` | Carry out the request, but spell out the trade-off in the reply before writing code. |
| `ask` | **Stop.** List the missing decisions and wait for the user to answer. Do not write code. |
| `reject` | **Stop.** Explain why the team has decided against this approach. Do not write code. |

### 7. Capture new knowledge — invisibly

If during the reply the user states a new rule, convention, or domain principle, capture it WITHOUT asking permission (it lands as pending for review):

- structured guidance → `save_skill(name, description, body)`
- single decision with reasoning → `remember_team_decision(domain, title, decision, reason)`
- inferred context that needs human ratification → `remember_business_context(domain, title, body)`

**Diff before you write** (see the tool docstrings) — re-call with the same title to refresh stale entries, never create near-duplicates.

### 8. Validate before shipping (if you wrote code)

If your reply includes code changes, call `validate_generated_code(code)` before posting the diff. Fix every blocker it reports, then re-validate.

---

**Why this slash command exists:** MCP tool descriptions only show up when Claude decides to use a tool. Plain prompts can slip past the pipeline. `/knowai` forces the consult so the user always sees a Risk header, the relevant memory, and the reusable assets — no guessing whether the AI checked.

The user's actual request is below:
