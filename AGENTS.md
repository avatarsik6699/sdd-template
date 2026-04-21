# Agent rules for working on the `sdd-template` repository itself

> This repository IS the template. You are maintaining reusable scaffolding, not building a product.
> The canonical rules that ship to **derived projects** live in [`human-instructions/AGENTS.for-new-projects.md`](human-instructions/AGENTS.for-new-projects.md).
> This file only covers how to change the template.

## Template Repo Scope

- Do not treat `docs/` as live requirements — they are template files with `[PLACEHOLDERS]`.
- Do not run `/phase-gate`, `/phase-init`, `/spec-sync`, or `/context-update` here. Those skills are for derived projects. Test them in a scratch directory.
- A change belongs in this repo only if it improves the template for future projects.
- Keep references consistent across `README.md`, `CLAUDE.md`, `AGENTS.md`, `human-instructions/`, `.claude/skills/`, and `plugins/sdd-workflow/`.

## Source of Truth Map

When you change workflow behavior, edit the canonical playbook — never the wrapper.

| Concern | Canonical source |
|---|---|
| Workflow procedure (phase-init, phase-gate, spec-sync, context-update) | [`docs/workflows/*.md`](docs/workflows/) |
| Rules that ship to derived projects | [`human-instructions/AGENTS.for-new-projects.md`](human-instructions/AGENTS.for-new-projects.md) |
| Claude-specific adapter for derived projects | [`human-instructions/CLAUDE.for-new-projects.md`](human-instructions/CLAUDE.for-new-projects.md) |
| Stack-specific commands (incl. gate commands) | [`docs/STACK.md`](docs/STACK.md) |
| Recurring pitfalls & permission-denied protocol | [`docs/KNOWN_GOTCHAS.md`](docs/KNOWN_GOTCHAS.md) |

Runtime wrappers (`.claude/skills/*/SKILL.md`, `plugins/sdd-workflow/{skills,commands}/*.md`) are thin stubs that point at `docs/workflows/`.

## Library Documentation Lookup

Before writing or reviewing code that uses an external library, use up-to-date docs in this order: Context7 via MCP (if available) → `ctx7` CLI → official docs. Do not rely on training-data knowledge alone.

## Filesystem Permission Failures

On `EACCES` / `EPERM` / "Permission denied" / "Read-only file system", **stop immediately** and follow the handoff protocol in [`docs/KNOWN_GOTCHAS.md § Docker-owned files`](docs/KNOWN_GOTCHAS.md#docker-owned-files-break-host-operations-eacces--eperm--read-only). Never `sudo`, `chmod -R 777`, delete-and-recreate, or silently loop.

## Git Workflow (for the template itself)

- Branch from `main`: `fix/description` or `feat/description`. No `feat/phase-N` branches here — that convention is for derived projects.
- Conventional commits: `feat|fix|chore|docs|refactor(scope): description`.
- No direct push to `main` — open a PR.
- No `--force`, `reset --hard`, or `--no-verify` without explicit user instruction.

## What "done" means

- Template files are internally consistent (no broken references, no stale placeholders).
- The two derived-project files (`human-instructions/AGENTS.for-new-projects.md`, `human-instructions/CLAUDE.for-new-projects.md`) reflect intended behavior.
- Skill wrappers under `.claude/skills/` and `plugins/sdd-workflow/` still resolve to the canonical playbook.
- `README.md` reflects any structural changes.
