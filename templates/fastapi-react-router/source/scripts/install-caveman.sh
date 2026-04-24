#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  ./scripts/install-caveman.sh [agent] [--copy]

Examples:
  ./scripts/install-caveman.sh
  ./scripts/install-caveman.sh codex
  ./scripts/install-caveman.sh cursor --copy
  ./scripts/install-caveman.sh claude-code

Notes:
  - agent defaults to auto-detection through npx skills
  - --copy avoids symlink issues on some Windows setups
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

AGENT="${1:-auto}"
COPY_FLAG="${2:-}"

if [[ "$AGENT" == "claude-code" ]]; then
  if ! command -v claude >/dev/null 2>&1; then
    echo "Error: claude CLI not found. Install Claude Code CLI first." >&2
    exit 1
  fi

  claude plugin marketplace add JuliusBrussee/caveman
  claude plugin install caveman@caveman
else
  if ! command -v npx >/dev/null 2>&1; then
    echo "Error: npx not found. Install Node.js first." >&2
    exit 1
  fi

  cmd=(npx -y skills@latest add JuliusBrussee/caveman)
  if [[ "$AGENT" != "auto" ]]; then
    cmd+=(-a "$AGENT")
  fi
  if [[ "$COPY_FLAG" == "--copy" ]]; then
    cmd+=(--copy)
  fi

  "${cmd[@]}"
fi

cat <<'EOF'

Installed Caveman.
Activation:
  - Claude/Gemini/Codex with hooks: automatic if runtime/plugin supports hooks
  - Other agents: run /caveman (Codex: $caveman) when needed

Recommended policy for this template:
  - keep Caveman opt-in/manual by default
  - use it for high-volume debugging loops
  - disable for final specs/architecture docs if you need verbose handoff text
EOF
