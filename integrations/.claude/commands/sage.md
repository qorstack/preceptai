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
3. **Find reusable assets.** Search the same files for services, utils, or
   components the team already has. Use them.
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
