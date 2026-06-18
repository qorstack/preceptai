---
trigger: manual
---

# sage-search-skill — research best practices and write them as team skills

When asked to run **sage-search-skill** or "research skills for this project":

1. **Map the project.** Read root config files and a sample of source files.
   Identify: stack, framework(s), domains, and what's already in `agents/sage/`.

2. **Research current best practices** for this exact stack. Focus on:
   UI/component patterns, minimal code (YAGNI, SRP), code quality, performance,
   and patterns trending in the last 12 months. Prefer specific and opinionated
   guidance over generic advice.

3. **Write skill entries** to `agents/sage/<domain>/skills/<slug>.md`:
   ```markdown
   ---
   id: <slug>
   type: skill
   title: <short title>
   domain: <domain>
   status: proposed
   source: ai
   enforcement: advise
   tags: [<tag>, ...]
   ---

   <one-paragraph explanation — what, why, when>

   **Do:** concrete example
   **Avoid:** anti-pattern
   ```
   One idea per file. Never duplicate existing entries. Update stale ones in place.

4. **Report** what was written. The dev reviews and flips `status: approved`.
