---
name: phase-gate
description: Run all gate checks for the current phase before committing. Checks docker infrastructure, pytest, tsc, vitest, and a smoke endpoint. Reports PASS or FAIL.
allowed-tools: Bash, Read
argument-hint: "[phase number, e.g. 01]"
---

You are running the SDD phase gate checks. Your job is to run all required checks and produce an honest PASS / FAIL report. Do NOT modify any code files — this skill is read-only.

**Target phase**: $ARGUMENTS

## Step 1 — Identify the phase file

If `$ARGUMENTS` is provided, read `docs/PHASE_$ARGUMENTS.md`.
If no argument, read `docs/STATE.md` and find the phase with status `🔄 in-progress`. Then read that phase file.
If neither resolves, ask: "Which phase number should I check? (e.g. /phase-gate 01)"

## Step 2 — Read gate commands

From the "Gate Checks" section of the phase file, note:
- Any smoke test URL and expected response
- Any phase-specific commands beyond the standard set

## Step 3 — Check infrastructure

```bash
docker compose ps
```

Verify `db` and `redis` containers are running and healthy.
If they are not healthy, run:
```bash
docker compose up -d db redis
```
Wait for healthy status. If they fail to become healthy after 30 seconds, report ❌ and stop.

## Step 4 — Run backend tests

```bash
uv run pytest tests/ -v 2>&1
```

Capture full output. Count passed / failed / error.
If ANY test fails or errors: record ❌, note the failing test names. Do NOT stop — continue to next checks so the full picture is visible.

## Step 5 — Run TypeScript check

```bash
cd frontend && pnpm exec tsc --noEmit 2>&1
```

Count errors. If any errors: record ❌ with error count.

## Step 6 — Run frontend tests

```bash
cd frontend && pnpm vitest run 2>&1
```

Count passed / failed. If any fail: record ❌.

## Step 7 — Run smoke test

Run the `curl` command from the phase file's Gate Checks section. If no smoke test is listed, use:
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/health
```
Expected: HTTP 200. If backend is not running, report ❌ with note "backend not running".

## Step 8 — Produce gate report

Output in this exact format:

```
## Phase Gate Report — PHASE_[XX]

| Check          | Status | Details                    |
|----------------|--------|----------------------------|
| Docker db      | ✅/❌  |                            |
| Docker redis   | ✅/❌  |                            |
| pytest         | ✅/❌  | N passed, M failed         |
| tsc --noEmit   | ✅/❌  | N errors                   |
| vitest         | ✅/❌  | N passed, M failed         |
| Smoke test     | ✅/❌  | HTTP NNN                   |

**Overall: ✅ PASS / ❌ FAIL**
```

If **PASS**: confirm it is safe to commit with the atomic commit message from the phase file.

If **FAIL**: list each failed check with the specific error output. Do NOT suggest committing. Suggest fixes where obvious.

## Rules
- Do not run `docker compose down` or any destructive command
- Do not edit any files
- Do not commit
- Report every check even if a previous one failed — give the full picture
