# Rules for developing the sdd-template repository itself

> **IMPORTANT**: This repository IS the template. You are not building a product here —
> you are maintaining reusable scaffolding. The `docs/` folder contains **template files**
> (filled with `[PLACEHOLDERS]`), not an active project specification.
> Do NOT treat them as live requirements.

---

## 1. What this repo is

`sdd-template` is a starter kit for AI-assisted phased development. Its artefacts:

| Path | What it is |
|------|-----------|
| `AGENTS.md` | Model-agnostic rules for working on the template |
| `CLAUDE.md` | Meta-rules for working on the template (this file) |
| `human-instructions/AGENTS.for-new-projects.md` | The AGENTS.md that gets copied into every derived project |
| `human-instructions/CLAUDE.for-new-projects.md` | The CLAUDE.md that gets copied into every derived project |
| `docs/SPEC.md` | Example / blank SPEC for derived projects — a template file |
| `docs/CONTEXT.md` | Example CONTEXT for derived projects — a template file |
| `docs/STATE.md` | Example STATE tracker — a template file |
| `docs/PHASE_TEMPLATE.md` | Scaffold for generating PHASE_XX.md in derived projects |
| `docs/PHASE_01.md` | Reference example phase — a template file |
| `docs/STACK.md` | Stack-specific companion to `README.md` (setup, testing, layout for the FastAPI + Nuxt reference stack). Replace when swapping stacks. |
| `docs/ARCHITECTURE.md` | Optional repo-memory file for system shape, boundaries, and responsibilities |
| `docs/DECISIONS.md` | Optional repo-memory file for ADR-style technical decisions |
| `docs/TESTING.md` | Optional repo-memory file for the real validation strategy |
| `docs/RUNBOOK.md` | Optional repo-memory file for operational commands and recovery steps |
| `docs/KNOWN_GOTCHAS.md` | Optional repo-memory file for recurring pitfalls and local traps |
| `app/`, `frontend/`, `tests/` | Reference implementation code shipped with the template |
| `.claude/` | Claude Code specific skill definitions (`skills/`) used by derived projects |

---

## 2. Rules specific to template development

1. **Do not follow phase-gate rules** — `/phase-gate`, `/phase-init`, `/context-update`,
   `/spec-sync` are skills *for derived projects*. Do not run them here unless you are
   testing the skills themselves.

2. **Do not treat `docs/` as active specs** — `[PLACEHOLDERS]` in those files are
   intentional. Never fill them in or delete them.

3. **Scope of a change** — ask yourself: "Does this improve the template for all future
   projects?" If yes, proceed. If it's project-specific, it doesn't belong here.

4. **Consistency across template files** — when you rename a skill, update all references:
   `CLAUDE.md` (this file), `human-instructions/CLAUDE.for-new-projects.md`, skill files
   under `.claude/skills/`, and `README.md`.

5. **No secrets, no hardcodes** — same rule as in any project.

---

## 3. Git workflow for this repo

- Branch from `main`: `git checkout -b fix/description` or `feat/description`
- Conventional commits: `feat|fix|chore|docs|refactor(scope): description`
- No `feat/phase-N` branches — that convention is for derived projects
- Do not push directly to `main` without a PR

---

## 4. What "done" means here

A change to the template is done when:
- [ ] Template files are internally consistent (no broken references, no stale placeholders)
- [ ] `human-instructions/CLAUDE.for-new-projects.md` matches the intended derived-project rules
- [ ] Skills under `.claude/skills/` work correctly when invoked
- [ ] `README.md` reflects any structural changes

---

## 5. Skills available in this repo

These skills are defined here and shipped to derived projects:

| Skill | Purpose |
|-------|---------|
| `spec-sync` | Sync SPEC.md changes across docs — **for derived projects** |
| `phase-gate` | Run gate checks before commit — **for derived projects** |
| `context-update` | Update CONTEXT.md after phase — **for derived projects** |
| `phase-init` | Scaffold a new PHASE_XX.md, filling scope, Contracts, and Files from SPEC.md — **for derived projects** |

When **testing** a skill, use a scratch directory, not this repo's `docs/`.
