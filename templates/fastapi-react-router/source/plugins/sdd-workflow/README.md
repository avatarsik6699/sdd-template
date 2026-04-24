# SDD Workflow Codex Plugin

This plugin makes the repository's SDD workflow visible to Codex as native:

- skills under `skills/`
- slash commands under `commands/`
- project-local MCP expectations via `.mcp.json`
- a reference Codex hook config in `hooks.json`

## What this adds

- `/phase-init`
- `/phase-gate`
- `/context-update`
- `/spec-sync`

The plugin mirrors the intent of the existing Claude setup in `.claude/skills/`,
but uses Codex-native plugin discovery through:

- [`.agents/plugins/marketplace.json`](../../.agents/plugins/marketplace.json)
- [`.codex-plugin/plugin.json`](./.codex-plugin/plugin.json)

## Hooks

Codex runtime hooks are enabled through project-scoped config in
[`../../.codex/config.toml`](../../.codex/config.toml) and loaded from
[`../../.codex/hooks.json`](../../.codex/hooks.json). The plugin-local
[`hooks.json`](./hooks.json) is kept as a reference copy for the workflow
bundle; current Codex plugin manifests do not load hooks directly.

The active hook only covers `PreToolUse` for `Bash`. Codex currently does not
emit `Write`, `Edit`, or `MultiEdit` for `PostToolUse`, so format-on-write hooks
cannot be implemented through the current hooks API.

## Context7

The plugin declares a project-local `context7` MCP server in [`.mcp.json`](./.mcp.json).
In this workspace, Codex also has a global MCP entry already configured, which is
the most reliable option when the `context7-mcp` binary is not on PATH.

Recommended docs lookup order for this project:

1. `context7` via MCP
2. `ctx7` CLI fallback
3. Official docs only when Context7 is unavailable

See:

- [docs/AGENT_SETUP.md](../../docs/AGENT_SETUP.md)
- [AGENTS.md](../../AGENTS.md)

## Restart requirement

After adding or changing plugin files, restart Codex in this workspace so the
plugin, slash commands, and marketplace entry are reloaded.

After adding or changing `.codex/config.toml` or `.codex/hooks.json`, restart
Codex so runtime hooks are reloaded.
