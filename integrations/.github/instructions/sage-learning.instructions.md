---
applyTo: "agents/sage/**"
---

# Sage Learning

When asked to "learn this codebase" or run sage-learning:

Study how **this team actually writes code** and turn it into Sage knowledge, so
every future agent writes code that matches them. Run once per repo, and again
after big refactors. Everything you find is saved under `agents/sage/`.

1. **Map the repo.** Identify domains, the stack, and conventions in use —
   naming, error handling, folder layout, logging, testing, repeated patterns.
2. **Find the reusable assets.** Services, utils, components the team already
   has — what new code should reuse instead of reinventing.
3. **Spot the rules-in-practice.** Each consistent pattern is a candidate rule.
4. **Write it to `agents/sage/`** (format in `AGENTS.md` §2):
   - per-domain `rules.md`; `decisions/<slug>.md`; update relevant role files.
5. **Diff before writing**: never duplicate an existing entry; update in place.

Tell the dev what you captured. They review and flip `status: approved`.
