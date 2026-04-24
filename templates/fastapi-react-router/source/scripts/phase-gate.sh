#!/usr/bin/env bash

set -u

usage() {
  cat <<'EOF'
Usage: ./scripts/phase-gate.sh [PHASE_NUMBER]

Runs the portable phase gate:
- starts the full Docker Compose stack
- waits for service health
- runs Alembic migrations inside the backend container
- runs backend/frontend checks from the host
- runs Playwright e2e against the local stack
- reports PASS only when all checks are green and architect notes are resolved
EOF
}

if [[ "${1:-}" =~ ^(-h|--help)$ ]]; then
  usage
  exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="${SDD_PROJECT_ROOT:-$(dirname "$SCRIPT_DIR")}"
cd "$ROOT_DIR"

PHASE_NUMBER="${1:-}"
if [[ -z "$PHASE_NUMBER" ]]; then
  PHASE_NUMBER="$(python3 - <<'PY'
from pathlib import Path
import re

state_path = Path("docs/STATE.md")
if not state_path.exists():
    raise SystemExit("")

for line in state_path.read_text().splitlines():
    if "in-progress" not in line:
        continue
    match = re.search(r"PHASE[_ ](\d+)", line, re.IGNORECASE)
    if match:
        print(match.group(1).zfill(2))
        break
PY
)"
fi

if [[ -z "$PHASE_NUMBER" ]]; then
  echo "Could not infer the phase number from docs/STATE.md." >&2
  echo "Pass it explicitly, for example: ./scripts/phase-gate.sh 01" >&2
  exit 1
fi

PHASE_FILE="docs/PHASE_${PHASE_NUMBER}.md"
if [[ ! -f "$PHASE_FILE" ]]; then
  echo "Phase file not found: $PHASE_FILE" >&2
  exit 1
fi

if [[ ! -f .env ]]; then
  echo "Missing .env. Create it before running the phase gate." >&2
  exit 1
fi

STATUS_INFRA="FAIL"
STATUS_MIGRATIONS="FAIL"
STATUS_PYTEST="FAIL"
STATUS_FRONTEND_PREP="FAIL"
STATUS_TYPECHECK="FAIL"
STATUS_VITEST="FAIL"
STATUS_E2E_LINT="FAIL"
STATUS_E2E="FAIL"
STATUS_SMOKE="FAIL"
STATUS_ARCHITECT="FAIL"

DETAIL_INFRA=""
DETAIL_MIGRATIONS=""
DETAIL_PYTEST=""
DETAIL_FRONTEND_PREP=""
DETAIL_TYPECHECK=""
DETAIL_VITEST=""
DETAIL_E2E_LINT=""
DETAIL_E2E=""
DETAIL_SMOKE=""
DETAIL_ARCHITECT=""

SERVICE_NAMES=(db redis backend frontend nginx)

run_cmd() {
  local __output_var="$1"
  shift
  local output
  set +e
  output="$("$@" 2>&1)"
  local exit_code=$?
  set -e
  printf -v "$__output_var" '%s' "$output"
  return "$exit_code"
}

wait_for_stack() {
  local timeout_secs="${1:-120}"
  local deadline=$((SECONDS + timeout_secs))
  while (( SECONDS < deadline )); do
    if python3 - <<'PY'
import json
import subprocess
import sys

required = {
    "db": "healthy",
    "redis": "healthy",
    "backend": "healthy",
    "frontend": "healthy",
    "nginx": "running",
}

cmd = ["docker", "compose", "ps", "--format", "json"]
proc = subprocess.run(cmd, capture_output=True, text=True)
if proc.returncode != 0:
    sys.exit(1)

lines = [line for line in proc.stdout.splitlines() if line.strip()]
services = {}
for line in lines:
    item = json.loads(line)
    services[item["Service"]] = item

for service, expected in required.items():
    item = services.get(service)
    if not item:
        sys.exit(1)
    health = item.get("Health") or ""
    state = (item.get("State") or "").lower()
    if expected == "healthy":
        if health.lower() != "healthy":
            sys.exit(1)
    elif state != "running":
        sys.exit(1)
PY
    then
      return 0
    fi
    sleep 2
  done
  return 1
}

warm_up_stack() {
  local frontend_ok=1
  local backend_ok=1

  set +e
  curl -fsS http://localhost:3000/login >/dev/null
  frontend_ok=$?
  curl -fsS http://localhost:8000/api/v1/health >/dev/null
  backend_ok=$?
  set -e

  if [[ "$frontend_ok" -eq 0 && "$backend_ok" -eq 0 ]]; then
    sleep 8
    return 0
  fi

  return 1
}

ensure_stack_ready() {
  local reason="${1:-stack check}"

  if ! wait_for_stack 120; then
    echo "stack did not become healthy after ${reason}" >&2
    return 1
  fi

  if ! warm_up_stack; then
    echo "warm-up endpoints did not respond after ${reason}" >&2
    return 1
  fi

  return 0
}

count_architect_notes() {
  python3 - "$PHASE_FILE" <<'PY'
from pathlib import Path
import sys

phase_path = Path(sys.argv[1])
lines = phase_path.read_text().splitlines()
in_section = False
count = 0

for line in lines:
    if line.startswith("## Architect Review Notes"):
        in_section = True
        continue
    if in_section and line.startswith("## "):
        break
    if in_section and line.strip().startswith("- [ ]"):
        count += 1

print(count)
PY
}

extract_pytest_counts() {
  python3 - <<'PY'
import re
import sys

text = sys.stdin.read()
match = re.search(r"=+ .*? (\d+) passed(?:, (\d+) failed)?(?:, (\d+) errors?)?.*? =+", text)
if match:
    passed = int(match.group(1) or 0)
    failed = int(match.group(2) or 0)
    errors = int(match.group(3) or 0)
    print(f"{passed} passed, {failed} failed, {errors} errors")
else:
    print("see command output")
PY
}

extract_vitest_counts() {
  python3 - <<'PY'
import re
import sys

text = sys.stdin.read()
test_match = re.search(r"Tests\s+(\d+) passed(?:\s*\|\s*(\d+) failed)?", text)
if test_match:
    passed = int(test_match.group(1) or 0)
    failed = int(test_match.group(2) or 0)
    print(f"{passed} passed, {failed} failed")
else:
    print("see command output")
PY
}

parse_junit() {
  python3 - <<'PY'
from pathlib import Path
import xml.etree.ElementTree as ET

path = Path("frontend/test-results/junit.xml")
if not path.exists():
    print("missing")
    raise SystemExit(0)

root = ET.parse(path).getroot()
passed = failures = skipped = 0
failed_suites = []

for case in root.iter("testcase"):
    skipped_node = case.find("skipped")
    failure_node = case.find("failure")
    error_node = case.find("error")
    if skipped_node is not None:
        skipped += 1
    elif failure_node is not None or error_node is not None:
        failures += 1
        classname = case.attrib.get("classname") or case.attrib.get("file") or "unknown"
        if classname not in failed_suites:
            failed_suites.append(classname)
    else:
        passed += 1

details = f"{passed} passed, {failures} failed, {skipped} skipped"
if failed_suites:
    details += " — failed: " + ", ".join(failed_suites)
details += " — report: frontend/playwright-report/index.html"
print(details)
PY
}

extract_phase_smoke_override() {
  python3 - "$PHASE_FILE" <<'PY'
import base64
from pathlib import Path
import re
import sys

phase_path = Path(sys.argv[1])
text = phase_path.read_text()
match = re.search(
    r"Phase-specific smoke override:\s*```(?:bash)?\n(?P<body>.*?)```",
    text,
    re.DOTALL,
)
if not match:
    raise SystemExit(0)

command_lines = []
expected = ""

for raw_line in match.group("body").splitlines():
    line = raw_line.rstrip()
    stripped = line.strip()
    if not stripped:
        if command_lines:
            break
        continue
    if stripped.startswith("#"):
        if stripped.startswith("# expected:") and not expected:
            expected = stripped[len("# expected:"):].strip()
        continue
    command_lines.append(line)

if command_lines:
    command = "\n".join(command_lines)
    print(base64.b64encode(command.encode()).decode())
    print(base64.b64encode(expected.encode()).decode())
PY
}

set -e

STACK_OUTPUT=""
if run_cmd STACK_OUTPUT docker compose up -d; then
  if ensure_stack_ready "docker compose up -d"; then
    STATUS_INFRA="PASS"
    DETAIL_INFRA="docker compose stack is up; db/redis/backend/frontend healthy, nginx running"
  else
    STATUS_INFRA="FAIL"
    DETAIL_INFRA="stack did not become healthy and warm after docker compose up -d"
  fi
else
  STATUS_INFRA="FAIL"
  DETAIL_INFRA="$(printf '%s' "$STACK_OUTPUT" | tail -n 1)"
fi

ARCHITECT_COUNT="$(count_architect_notes)"
if [[ "$ARCHITECT_COUNT" == "0" ]]; then
  STATUS_ARCHITECT="PASS"
  DETAIL_ARCHITECT="0 unchecked items"
else
  STATUS_ARCHITECT="FAIL"
  DETAIL_ARCHITECT="${ARCHITECT_COUNT} unchecked items"
fi

MIGRATIONS_OUTPUT=""
if [[ "$STATUS_INFRA" == "PASS" ]] && run_cmd MIGRATIONS_OUTPUT docker compose exec -T backend uv run alembic upgrade head; then
  STATUS_MIGRATIONS="PASS"
  DETAIL_MIGRATIONS="uv run alembic upgrade head succeeded in backend container"
else
  STATUS_MIGRATIONS="FAIL"
  DETAIL_MIGRATIONS="$(printf '%s' "$MIGRATIONS_OUTPUT" | tail -n 1)"
fi

PYTEST_OUTPUT=""
if run_cmd PYTEST_OUTPUT uv run pytest tests/ -v; then
  STATUS_PYTEST="PASS"
else
  STATUS_PYTEST="FAIL"
fi
DETAIL_PYTEST="$(printf '%s' "$PYTEST_OUTPUT" | extract_pytest_counts)"

FRONTEND_PREP_OUTPUT=""
if run_cmd FRONTEND_PREP_OUTPUT bash -lc 'cd frontend && pnpm typecheck'; then
  FRONTEND_RESTART_OUTPUT=""
  STACK_REFRESH_OUTPUT=""
  if run_cmd FRONTEND_RESTART_OUTPUT docker compose restart frontend \
    && run_cmd STACK_REFRESH_OUTPUT ensure_stack_ready "frontend restart after pnpm typecheck"; then
    STATUS_FRONTEND_PREP="PASS"
    DETAIL_FRONTEND_PREP="validated frontend graph, restarted frontend, and re-warmed stack"
  else
    STATUS_FRONTEND_PREP="FAIL"
    DETAIL_FRONTEND_PREP="$(
      {
        printf '%s\n' "$FRONTEND_RESTART_OUTPUT"
        printf '%s\n' "$STACK_REFRESH_OUTPUT"
      } | tail -n 1
    )"
  fi
else
  STATUS_FRONTEND_PREP="FAIL"
  DETAIL_FRONTEND_PREP="$(printf '%s' "$FRONTEND_PREP_OUTPUT" | tail -n 1)"
fi

TYPECHECK_OUTPUT=""
if run_cmd TYPECHECK_OUTPUT bash -lc 'cd frontend && pnpm exec tsc --noEmit'; then
  STATUS_TYPECHECK="PASS"
  DETAIL_TYPECHECK="0 errors"
else
  STATUS_TYPECHECK="FAIL"
  DETAIL_TYPECHECK="$(printf '%s' "$TYPECHECK_OUTPUT" | tail -n 1)"
fi

VITEST_OUTPUT=""
if run_cmd VITEST_OUTPUT bash -lc 'cd frontend && pnpm vitest run'; then
  STATUS_VITEST="PASS"
else
  STATUS_VITEST="FAIL"
fi
DETAIL_VITEST="$(printf '%s' "$VITEST_OUTPUT" | extract_vitest_counts)"

E2E_LINT_OUTPUT=""
if run_cmd E2E_LINT_OUTPUT bash -lc 'cd frontend && pnpm test:e2e:lint'; then
  STATUS_E2E_LINT="PASS"
  DETAIL_E2E_LINT="anti-flake policy enforced"
else
  STATUS_E2E_LINT="FAIL"
  DETAIL_E2E_LINT="$(printf '%s' "$E2E_LINT_OUTPUT" | tail -n 1)"
fi

E2E_OUTPUT=""
rm -f frontend/test-results/junit.xml
if run_cmd E2E_OUTPUT bash -lc 'cd frontend && CI=1 pnpm test:e2e --project=chromium'; then
  STATUS_E2E="PASS"
else
  STATUS_E2E="FAIL"
fi
DETAIL_E2E="$(parse_junit)"
if [[ "$DETAIL_E2E" == "missing" ]]; then
  DETAIL_E2E="Playwright did not emit junit.xml — check reporter config"
fi

SMOKE_OVERRIDE="$(
  extract_phase_smoke_override
)"
SMOKE_COMMAND="curl -sS http://localhost:8000/api/v1/health"
SMOKE_EXPECTED='"status":"ok"'
if [[ -n "$SMOKE_OVERRIDE" ]]; then
  mapfile -t SMOKE_OVERRIDE_LINES <<<"$SMOKE_OVERRIDE"
  if [[ "${#SMOKE_OVERRIDE_LINES[@]}" -ge 1 && -n "${SMOKE_OVERRIDE_LINES[0]}" ]]; then
    SMOKE_COMMAND="$(
      printf '%s' "${SMOKE_OVERRIDE_LINES[0]}" \
        | python3 -c 'import base64, sys; print(base64.b64decode(sys.stdin.read()).decode(), end="")'
    )"
  fi
  if [[ "${#SMOKE_OVERRIDE_LINES[@]}" -ge 2 && -n "${SMOKE_OVERRIDE_LINES[1]}" ]]; then
    SMOKE_EXPECTED="$(
      printf '%s' "${SMOKE_OVERRIDE_LINES[1]}" \
        | python3 -c 'import base64, sys; print(base64.b64decode(sys.stdin.read()).decode(), end="")'
    )"
  fi
fi

SMOKE_OUTPUT=""
if run_cmd SMOKE_OUTPUT bash -lc "$SMOKE_COMMAND"; then
  if [[ -n "$SMOKE_EXPECTED" ]]; then
    if [[ "$SMOKE_OUTPUT" == *"$SMOKE_EXPECTED"* ]]; then
      STATUS_SMOKE="PASS"
      DETAIL_SMOKE="$SMOKE_OUTPUT"
    else
      STATUS_SMOKE="FAIL"
      DETAIL_SMOKE="unexpected response: $SMOKE_OUTPUT"
    fi
  else
    STATUS_SMOKE="PASS"
    DETAIL_SMOKE="$SMOKE_OUTPUT"
  fi
else
  STATUS_SMOKE="FAIL"
  DETAIL_SMOKE="$(printf '%s' "$SMOKE_OUTPUT" | tail -n 1)"
fi

overall="PASS"
for status in \
  "$STATUS_INFRA" "$STATUS_MIGRATIONS" "$STATUS_PYTEST" "$STATUS_FRONTEND_PREP" \
  "$STATUS_TYPECHECK" "$STATUS_VITEST" "$STATUS_E2E_LINT" "$STATUS_E2E" "$STATUS_SMOKE" "$STATUS_ARCHITECT"; do
  if [[ "$status" != "PASS" ]]; then
    overall="FAIL"
    break
  fi
done

echo "## Phase Gate Report — PHASE_${PHASE_NUMBER}"
echo
echo "| Check | Status | Details |"
echo "|---|---|---|"
echo "| Infrastructure | ${STATUS_INFRA} | ${DETAIL_INFRA} |"
echo "| Migrations | ${STATUS_MIGRATIONS} | ${DETAIL_MIGRATIONS} |"
echo "| Backend tests | ${STATUS_PYTEST} | ${DETAIL_PYTEST} |"
echo "| Frontend prep | ${STATUS_FRONTEND_PREP} | ${DETAIL_FRONTEND_PREP} |"
echo "| Frontend type check | ${STATUS_TYPECHECK} | ${DETAIL_TYPECHECK} |"
echo "| Frontend unit tests | ${STATUS_VITEST} | ${DETAIL_VITEST} |"
echo "| E2E anti-flake lint | ${STATUS_E2E_LINT} | ${DETAIL_E2E_LINT} |"
echo "| E2E | ${STATUS_E2E} | ${DETAIL_E2E} |"
echo "| Smoke test | ${STATUS_SMOKE} | ${DETAIL_SMOKE} |"
echo "| Architect review | ${STATUS_ARCHITECT} | ${DETAIL_ARCHITECT} |"
echo
echo "**Overall: ${overall}**"

if [[ "$STATUS_ARCHITECT" == "FAIL" ]]; then
  echo
  echo "Open architect review notes:"
  python3 - "$PHASE_FILE" <<'PY'
from pathlib import Path
import sys

phase_path = Path(sys.argv[1])
lines = phase_path.read_text().splitlines()
in_section = False

for line in lines:
    if line.startswith("## Architect Review Notes"):
        in_section = True
        continue
    if in_section and line.startswith("## "):
        break
    if in_section and line.strip().startswith("- [ ]"):
        print(line.strip())
PY
fi

if [[ "$overall" == "PASS" ]]; then
  exit 0
fi
exit 1
