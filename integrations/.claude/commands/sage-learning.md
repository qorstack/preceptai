# /sage-learning — learn this codebase into Sage knowledge

Study how **this team actually writes code** and turn it into Sage knowledge, so
every future agent writes code that matches them. Run once per repo, and again
after big refactors. Everything you find is saved under `agents/sage/`.

Do this:

1. **Map the repo.** Identify the domains (e.g. `billing`, `search`), the stack,
   and the conventions actually in use — naming, error handling, folder layout,
   logging, testing, the patterns the team repeats.
2. **Find the reusable assets and read them — do not guess.** Services, utils,
   components, base classes the team already has. For each one:
   - **Open the file and read its exports** — function signatures, parameter
     shapes, option types, and return types. Do not infer these from the file
     name or folder; only the source is authoritative.
   - Document the full API in the matching `decisions/<slug>.md` so future
     agents can read the decision instead of having to open the source. Include
     a table of every exported symbol with its purpose and key options.
   - Flag when an asset covers more use-cases than its name suggests (e.g. a
     "TextField" validator that also handles radio/select string values).
3. **Spot the rules-in-practice.** What does the code consistently do (and
   avoid)? Each consistent pattern is a candidate rule.
4. **Write it to `agents/sage/`** (format in `AGENTS.md` §2):
   - per-domain `rules.md` — the conventions + reusable assets for that domain;
   - `decisions/<slug>.md` for notable patterns worth enforcing
     (`enforcement: advise` unless it's clearly a must), `source: ai`,
     `status: proposed`;
   - update `roles/role-<lens>.md` → its `Good at` with the stack/patterns you found.
5. **Diff before writing** (`AGENTS.md` §3): never duplicate an existing entry;
   update a stale one in place. One idea per file.

Then tell the dev what you captured, in one list. They review and flip
`status: approved`. This is how Sage learns to code like the team — re-run it
whenever the codebase shifts.
