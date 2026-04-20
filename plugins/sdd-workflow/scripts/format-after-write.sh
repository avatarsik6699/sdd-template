#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/../../.." && pwd)"
payload="$(cat || true)"

target_file="$(python3 - <<'PY' "$payload"
import json
import sys

raw = sys.argv[1] if len(sys.argv) > 1 else ""
path = ""
if raw:
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            tool_input = data.get("tool_input", {})
            if isinstance(tool_input, dict):
                path = (
                    tool_input.get("file_path")
                    or tool_input.get("new_file_path")
                    or tool_input.get("path")
                    or ""
                )
            if not path:
                path = (
                    data.get("file_path")
                    or data.get("new_file_path")
                    or data.get("path")
                    or ""
                )
    except Exception:
        path = ""
print(path)
PY
)"

if [ -z "$target_file" ]; then
  exit 0
fi

case "$target_file" in
  *.ts|*.tsx|*.vue)
    cd "$repo_root"
    pnpm exec prettier --write "$target_file" >/dev/null 2>&1 || true
    ;;
  *.py)
    cd "$repo_root"
    uv run ruff format "$target_file" >/dev/null 2>&1 || true
    ;;
esac
