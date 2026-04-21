> **TEMPLATE FILE** — Copy this file to the root of a new project as `CLAUDE.md`.
> Replace `[PROJECT_NAME]` with the actual project name.
> This is a thin Claude-specific wrapper. The canonical rules live in `AGENTS.md`.

---

# [PROJECT_NAME] — Claude Code adapter

**Start here:** read [`AGENTS.md`](AGENTS.md). It is the source of truth for all process rules — scope lock, gates, library lookup, git workflow, permission-denied handling, spec-sync protocol, CONTEXT.md version rules, and phase lifecycle.

This file only adds Claude-specific items.

## Slash commands (Claude Code skills)

| Command | When to use | Wraps workflow |
|---------|-------------|----------------|
| `/phase-init [N]` | Scaffold the next `docs/PHASE_XX.md` from SPEC | [docs/workflows/phase-init.md](docs/workflows/phase-init.md) |
| `/phase-gate [N]` | Validate a phase before committing | [docs/workflows/phase-gate.md](docs/workflows/phase-gate.md) |
| `/spec-sync [description]` | Immediately after editing `docs/SPEC.md` | [docs/workflows/spec-sync.md](docs/workflows/spec-sync.md) |
| `/context-update [N]` | After the gate passes | [docs/workflows/context-update.md](docs/workflows/context-update.md) |

Skill wrappers live in `.claude/skills/` and are intentionally thin — they just point at the playbooks in `docs/workflows/`.

## MCP and Context7 setup

Per `AGENTS.md § Library Documentation Lookup`, prefer Context7 via MCP when available. For one-time MCP configuration notes (both Claude Code and Codex), see [docs/AGENT_SETUP.md](docs/AGENT_SETUP.md).
