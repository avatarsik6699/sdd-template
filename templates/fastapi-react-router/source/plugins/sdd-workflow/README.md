# SDD Workflow Codex Plugin

This plugin makes the repository's SDD workflow visible to Codex as native:

- skills under `skills/`
- slash commands under `commands/`
- project-local MCP expectations via `.mcp.json`
- a reference Codex hook config in `hooks.json`

## What this adds

- `/spec-init`
- `/phase-init`
- `/phase-gate`
- `/context-update`
- `/spec-sync`

The plugin mirrors the intent of the existing Claude setup in `.claude/skills/`,
but uses Codex-native plugin discovery through:

- [`.agents/plugins/marketplace.json`](../../.agents/plugins/marketplace.json)
- [`.codex-plugin/plugin.json`](./.codex-plugin/plugin.json)

## Hooks

The plugin-local [`hooks.json`](./hooks.json) is a reference policy for the
workflow bundle. Current Codex plugin manifests do not load hooks directly.

If your workspace uses project-scoped Codex hook config, point it at this
plugin-local file.

The active hook only covers `PreToolUse` for `Bash`. Codex currently does not
emit `Write`, `Edit`, or `MultiEdit` for `PostToolUse`, so format-on-write hooks
cannot be implemented through the current hooks API.

## Docs MCPs

The plugin declares project-local docs MCP servers in [`.mcp.json`](./.mcp.json):

- `context7` (third-party library/framework docs)
- `openaiDeveloperDocs` (OpenAI platform/developer docs)

In this workspace, Codex can also use global MCP entries, which remain the most
reliable option when `context7-mcp` is not on PATH.

Recommended docs lookup order for this project:

1. `context7` via MCP for third-party library/framework docs
2. `openaiDeveloperDocs` via MCP for OpenAI platform/API docs
3. `ctx7` CLI fallback
4. Official docs only when MCP/CLI are unavailable

See:

- [docs/AGENT_SETUP.md](../../docs/AGENT_SETUP.md)
- [AGENTS.md](../../AGENTS.md)

## Restart requirement

After adding or changing plugin files, restart Codex in this workspace so the
plugin, slash commands, and marketplace entry are reloaded.

If you wire this reference into your own `.codex` hook config, restart Codex
after changing the hook files so runtime hooks are reloaded.
