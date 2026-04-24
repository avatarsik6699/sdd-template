# Agent rules for working on the `sdd-template` repository itself

> This repository IS the template. You are maintaining reusable scaffolding, not building a product.
> The canonical rules that ship to **derived projects** live in [`workflow/project-files/AGENTS.md.template`](workflow/project-files/AGENTS.md.template).
> This file only covers how to change the template.

## Template Repo Scope

- Do not treat `docs/` as live requirements — they are template files with `[PLACEHOLDERS]`.
- Do not run `/phase-gate`, `/phase-init`, `/spec-sync`, or `/context-update` here. Those skills are for derived projects. Test them in a scratch directory.
- A change belongs in this repo only if it improves the template for future projects.
- Keep references consistent across `README.md`, `CLAUDE.md`, `AGENTS.md`, `workflow/`, and the shipped runtime assets under `templates/fastapi-nuxt/source/`.

## Source of Truth Map

When you change workflow behavior, edit the canonical playbook — never the wrapper.

| Concern | Canonical source |
|---|---|
| Workflow procedure (phase-init, phase-gate, spec-sync, context-update) | [`workflow/docs/playbooks/*.md`](workflow/docs/playbooks/) |
| Rules that ship to derived projects | [`workflow/project-files/AGENTS.md.template`](workflow/project-files/AGENTS.md.template) |
| Claude-specific adapter for derived projects | [`workflow/project-files/CLAUDE.md.template`](workflow/project-files/CLAUDE.md.template) |
| Template manifests | `templates/<template-id>/template.yaml` |
| Template source snapshots | `templates/<template-id>/source/` |
| Stack-specific commands (incl. gate commands) | `templates/<template-id>/source/docs/STACK.md` |
| Recurring pitfalls & permission-denied protocol | `templates/<template-id>/source/docs/KNOWN_GOTCHAS.md` |

Runtime wrappers under `templates/<template-id>/source/.claude/skills/` and
`templates/<template-id>/source/plugins/sdd-workflow/` are thin stubs that point at
`workflow/docs/playbooks/`.

## Authoritative Source Rule

- `workflow/` is authoritative for reusable workflow assets.
- `templates/` is authoritative for extracted stack assets.
- `dev/` is generated and non-authoritative.
- Do not edit `dev/` as if it were canonical. Use it only as a disposable validation lab, and treat `sdd dev promote` as a classification tool for exceptional cases.
- The old derived-project instruction directory is gone and should not be reintroduced under a new compatibility path.
- Reusable behavior changes belong in canonical sources, never in compatibility stubs.
- The repository root is not a runnable product stack.
- Stack code, stack docs, deployment files, and shipped runtime assets belong under
  `templates/<template-id>/source/`, not at the repo root.

## Maintainer AI Skill

- The repo-specific maintainer skill lives at
  [`.codex/skills/template-repo-maintainer/SKILL.md`](.codex/skills/template-repo-maintainer/SKILL.md).
- Use it when the task is about changing `workflow/`, `templates/`, or the `sdd` CLI in this
  repository.
- It exists to reinforce the authoritative-source rule and the correct `sdd` validation loop for
  template-repo work.

## Library Documentation Lookup

Before writing or reviewing code that uses an external library, use up-to-date docs in this order: Context7 via MCP (if available) → `ctx7` CLI → official docs. Do not rely on training-data knowledge alone.

## Filesystem Permission Failures

On `EACCES` / `EPERM` / "Permission denied" / "Read-only file system", **stop immediately** and
follow the Docker-owned-files handoff protocol in the active template's `docs/KNOWN_GOTCHAS.md`.
Never `sudo`, `chmod -R 777`, delete-and-recreate, or silently loop.

## Git Workflow (for the template itself)

- Branch from `main`: `fix/description` or `feat/description`. No `feat/phase-N` branches here — that convention is for derived projects.
- Conventional commits: `feat|fix|chore|docs|refactor(scope): description`.
- No direct push to `main` — open a PR.
- No `--force`, `reset --hard`, or `--no-verify` without explicit user instruction.

## What "done" means

- Template files are internally consistent (no broken references, no stale placeholders).
- The two derived-project files (`workflow/project-files/AGENTS.md.template`, `workflow/project-files/CLAUDE.md.template`) reflect intended behavior.
- Shipped runtime wrappers under `templates/fastapi-nuxt/source/.claude/` and `templates/fastapi-nuxt/source/plugins/sdd-workflow/` still resolve to the canonical playbook.
- `README.md` reflects any structural changes.
