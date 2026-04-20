# Global Agent Rules

## What Is Portable Here

This repository contains two layers of agent guidance:

- `AGENTS.md` files: model-agnostic rules intended for any capable coding agent
- `CLAUDE.md` and `.claude/skills/`: Claude Code specific adapters, slash commands, and tool policies

When both exist, prefer this file for shared process rules and treat Claude-specific files as optional automation on top.

## Template Repo Scope

This repository is the template itself, not an active product.

- Do not treat `docs/` as live requirements. They are template files with placeholders.
- Only make changes that improve the template for future projects.
- Keep references consistent across `README.md`, `CLAUDE.md`, `AGENTS.md`, `human-instructions/`, and `.claude/skills/`.

## Documentation Lookup

Before writing or reviewing code that depends on an external library or framework, use an up-to-date documentation source.

Preferred order:
- a configured docs MCP/integration such as Context7, if available in the current agent runtime
- for OpenAI products specifically, the official OpenAI developer documentation MCP server, if available
- official library documentation
- primary-source docs or API references

Do not rely on stale model memory alone for library APIs.

## Repo Memory Files

Keep lightweight project memory in repository docs so different agent runtimes can recover the same high-signal context across sessions.

Recommended files:
- `docs/ARCHITECTURE.md` for system shape, boundaries, and responsibilities
- `docs/DECISIONS.md` for ADR-style technical decisions
- `docs/TESTING.md` for the real validation strategy and required checks
- `docs/RUNBOOK.md` for operational commands, deploy notes, and recovery steps
- `docs/KNOWN_GOTCHAS.md` for recurring pitfalls, edge cases, and local-environment traps

Keep these files concise and current. Prefer updating them over relying on conversational memory.

## Skills And Protocols

The workflow protocols in `.claude/skills/` are still useful even outside Claude Code, but they are not universally executable as native slash commands.

Portable interpretation:
- `spec-sync`: protocol for propagating `docs/SPEC.md` changes
- `phase-init`: protocol for scaffolding a new `docs/PHASE_XX.md`
- `phase-gate`: protocol for running validation checks before commit
- `context-update`: protocol for syncing `docs/CONTEXT.md`, `docs/STATE.md`, and `docs/CHANGELOG.md`

If an agent runtime does not support those skills natively, execute the corresponding markdown procedure manually.

Canonical portable playbooks live in `docs/workflows/`.
