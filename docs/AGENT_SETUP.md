# Agent Setup

This document defines the portable agent setup for this template across different coding runtimes.

## Documentation Lookup Policy

For third-party libraries and frameworks, use this order:

1. `Context7` via MCP, if the current agent runtime supports MCP and the server is configured
2. `ctx7` CLI via `npx ctx7@latest ...`
3. Official library documentation or primary-source docs

Do not rely on stale model memory alone for library APIs.

For OpenAI products and platform features, prefer the official OpenAI developer docs MCP server.

## Context7 Status Verified On 2026-04-20

On the machine used to validate this template:

- Claude Code has `context7` configured as an MCP server in `~/.claude/settings.json`
- Codex has `context7` configured as an MCP server in `~/.codex/config.toml`
- `ctx7` CLI is installed and authenticated: `npx ctx7@latest whoami` returned `Logged in`

## Claude Code

Example global config:

```json
{
  "mcpServers": {
    "context7": {
      "command": "/home/USER/.nvm/versions/node/vX.Y.Z/bin/context7-mcp"
    }
  }
}
```

## Codex

Preferred setup command:

```bash
codex mcp add context7 -- /home/USER/.nvm/versions/node/vX.Y.Z/bin/context7-mcp
codex mcp add openaiDeveloperDocs --url https://developers.openai.com/mcp
```

Example resulting config:

```toml
[mcp_servers.context7]
command = "/home/USER/.nvm/versions/node/vX.Y.Z/bin/context7-mcp"

[mcp_servers.openaiDeveloperDocs]
url = "https://developers.openai.com/mcp"
```

Useful commands:

```bash
codex mcp list
codex mcp get context7
codex mcp get openaiDeveloperDocs
codex mcp remove context7
codex mcp remove openaiDeveloperDocs
```

After changing Codex MCP config, restart Codex so the new MCP server is available in new sessions.

## CLI Fallback

If MCP is unavailable in the current runtime, use:

```bash
npx ctx7@latest library "<library name>" "<question>"
npx ctx7@latest docs /org/project "<question>"
```

Rules:

- Resolve the library ID with `library` first unless the `/org/project` ID is already known
- Use the official library name with correct punctuation
- Do not send secrets in queries
- If you hit quota or auth limits, run `npx ctx7@latest login` or set `CONTEXT7_API_KEY`

## Portable Recommendation

For multi-model projects:

- keep model-agnostic workflow rules in `AGENTS.md`
- keep runtime-specific adapters in `CLAUDE.md`, Codex config, and other agent-specific files
- store reusable workflow procedures in `docs/workflows/`
- prefer MCP when supported, but always document a CLI fallback
- add lightweight repo-memory docs such as `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, `docs/TESTING.md`, `docs/RUNBOOK.md`, and `docs/KNOWN_GOTCHAS.md`
