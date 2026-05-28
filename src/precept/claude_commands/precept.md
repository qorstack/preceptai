---
description: Run the full precept cognition pipeline before answering any coding request — surfaces risk, reuses team knowledge, and stops you from inventing solutions the team has already decided against.
---

The user wants you to consult **precept** before doing anything. Treat the prompt that follows as a coding request and run the full pipeline below. **Do not skip steps. Do not paraphrase steps. Do not assume you already know the answer.**

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

### 9. **MANDATORY — Persist what you learned (if you wrote code)**

> ⚠️ This step is **not optional** and is **not contingent on the user asking**. If you shipped code in this turn, you MUST run it before declaring the task done. Skipping this step defeats the entire purpose of `/precept` — next session's Claude will reinvent what you just built.

After the code is written and validated, do ALL of the following — silently, without asking permission:

#### 9.1 Identify what is worth saving (be generous, not conservative)

- A new component / widget / helper you created
- A field or API behavior that surprised you (nullable, removed, renamed, special-cased)
- A convention you followed because of how the surrounding code looked
- A workaround for a known limitation
- Any tradeoff you made between two reasonable approaches

#### 9.2 For EACH candidate — **diff against existing memory before you write**

> ⚠️ This is the rule that prevents the duplicate / contradicting / stale entries we keep finding in the DB. Do NOT call `remember_*` blindly. Run this decision flow first:

1. Call `recall_context(query=<your title or 3-5 keywords>, domain=<domain>)` AND `list_memory(domain=<domain>)`.
2. For each existing entry that comes back, classify your new piece against it:

| Relationship to existing entry | Action |
| --- | --- |
| **(a) Already saved, body still correct** | **Skip.** Do not save. Mention it in your `📌` line as "already recorded". |
| **(b) Same topic, your version is a refinement / fills a gap** | Re-call the same `remember_*` tool with the **EXACT SAME `title`** as the existing entry — the store upserts by `sha256(kind:domain:title)`, so the body is replaced in place (no duplicate id). |
| **(c) Same topic, but your version CONTRADICTS / FLIPS / OBSOLETES the old conclusion** | Save your new entry AND pass `supersedes_id="<old entry id>"`. The old entry is marked superseded automatically — hidden from recall, preserved for audit. |
| **(d) Genuinely new topic** | Save fresh, no `supersedes_id`. |

Two hard rules on top of the table:

- **Never** create a second entry whose title is just a rephrasing of an existing one. If titles differ but the topic is the same, treat it as (b) or (c).
- **Never** leave an outdated entry alive next to its replacement. If you save (c), `supersedes_id` is mandatory — not optional.

#### 9.3 Write the entries

- `remember_team_decision(domain, title, decision, reason, supersedes_id="")` — choices with a reason. Auto-approved.
- `remember_business_context(domain, title, body, tags="", supersedes_id="")` — facts about the system. Lands as pending.
- `save_skill(name, description, body)` — reusable how-to guidance.

Body text must be plain prose. **Do not include tool-call XML** (`<invoke>`, `<parameter>`, `</decision>`, `</body>` etc.) — the server strips known tool-call tags before storage, but you should write clean text in the first place.

#### 9.4 Refresh the scan

Call `refresh_scan(repo_path)` so the cognitive graph picks up new files/assets/conventions you just added.

#### 9.5 Report what happened

End your reply with one short line listing what got persisted, what got superseded, and what was already on file. Examples:

```text
📌 Saved: "Passport status banner pattern" (decision). Superseded: 5d50ea3e2a8da037 (old "buttons" rule). Already on file: "AppColors.warning palette". Scan refreshed.
```

```text
📌 Nothing new to persist this turn — all relevant rules already on file.
```

Do not silently skip the report line. The user is auditing whether you actually ran this step.

---

**Why this slash command exists:** MCP tool descriptions only show up when Claude decides to use a tool. Plain prompts can slip past the pipeline. `/precept` forces the consult so the user always sees a Risk header, the relevant memory, and the reusable assets — no guessing whether the AI checked. **Step 9 is the other half:** without it, precept becomes a one-way read and the graph never grows from the work you actually do.

The user's actual request is below:
