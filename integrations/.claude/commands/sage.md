# /sage — run the Sage cognition pipeline before coding

Run this before making any non-trivial code change.

## Step 1 — Establish your role

Before anything else, ask yourself (or the dev): **what role am I taking on this task?**

Choose the lens that fits:

| Role | When to use |
| --- | --- |
| **Dev** | Writing features, fixing bugs, refactoring |
| **Reviewer** | Auditing code correctness, security, style |
| **Architect** | Designing systems, evaluating approaches, big decisions |
| **Debugger** | Root-causing failures, reading logs, reproducing issues |

State it at the top of your reply: `Role: Dev — implementing X` (or whichever fits).
If the task crosses roles (e.g. design + implement), name the primary one.

## Step 2 — Run the cognition pipeline

1. **Understand the request.** What domain does it touch?
2. **Read domain knowledge.** Check `agents/sage/<domain>/rules.md` and relevant
   `decisions/` files. Follow what the team has already decided.
3. **Find reusable assets — then read them, never guess.** Search `rules.md`
   and `decisions/` for utilities, hooks, or components the team already has.
   When you find one:
   - **Open the source file and read its exports** before writing code that
     uses it. Never infer its API from its name or the decision description.
   - If the decision lists the full API (exported functions + parameter shapes),
     that is sufficient — but if anything is unclear or unlisted, read the
     source. Decision files can be stale; the source file is always authoritative.
   - A missing export in a decision file is a documentation gap, not proof the
     export doesn't exist.
4. **Assess risk.** What could break? What is the blast radius?

## Step 3 — State intent before writing

Format your pre-code output as:

```
Role: <role> — <one-line summary of what you're doing>

## Intent
<what this change does>

## Impact
<what it touches, what it might break>

## Risk
<LOW | MEDIUM | HIGH — and why>

## Plan
<brief steps before you write a line>
```

Then proceed. Skip this only for truly trivial edits (typos, comment fixes).
