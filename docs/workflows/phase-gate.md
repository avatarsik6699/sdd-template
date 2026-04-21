# phase-gate — Canonical Playbook

Run the validation checks for the current phase and produce an honest PASS / FAIL report that includes unresolved architect review notes.

This document is the single source of truth for the `phase-gate` workflow. Runtime wrappers point here.

**Stack coupling:** the concrete commands for each check live in [docs/STACK.md → Gate Commands](../STACK.md#gate-commands). This workflow is stack-agnostic — it describes *what* is checked and *how results are reported*, not *which* tool runs each check. Derived projects swapping stacks rewrite STACK.md only.

## Input

- Target phase number, or infer it from `docs/STATE.md` (the phase with status `🔄 in-progress`).

## Required reads

- `docs/PHASE_XX.md` — Gate Checks and Architect Review Notes sections
- `docs/STACK.md` — Gate Commands section (dispatch table)
- Optionally `docs/STATE.md` if no phase number was given

## Procedure

### 1. Identify the target phase

- If a phase number was provided, read `docs/PHASE_[XX].md`.
- Otherwise read `docs/STATE.md` and find the `🔄 in-progress` row.
- If neither resolves, ask: "Which phase number should I check? (e.g. /phase-gate 01)"

### 2. Gather per-phase expectations

From the phase file:

- **Gate Checks** — note any phase-specific smoke URL, expected response, or extra commands beyond the standard set.
- **Architect Review Notes** — collect every unchecked checklist item. Each unchecked item blocks PASS until resolved and checked off.

### 3. Load the dispatch table

From `docs/STACK.md → Gate Commands`, read the seven rows:

1. Infrastructure
2. Backend tests
3. Type generation
4. Frontend typecheck
5. Frontend unit
6. E2E
7. Smoke

Each row specifies the command, preconditions, and pass signal for that check.

### 4. Execute checks

Run each row in order. Record status (`✅` or `❌`) and a one-line detail (counts, error summary, etc.). Do **not** stop at the first failure — run every row so the full picture is visible to the architect.

Special handling:

- **Infrastructure**: if `db` / `redis` are not healthy, run the start command from the dispatch row, wait up to 30 seconds for healthy status, then record accordingly. If they never become healthy, mark ❌ and continue with later checks that do not depend on them.
- **E2E**: check preconditions *before* running. If the full app stack is not up, record ❌ for the e2e row with the note `stack not up — run docker compose up -d and re-run /phase-gate` and skip the Playwright command entirely. **Do not auto-start the stack** — silent auto-starts mask drift.
- **Smoke**: if the phase file specifies a smoke URL or expected response, use that; otherwise use the default from the dispatch row.

### 5. Evaluate architect review notes

Count unchecked items under the phase file's `Architect Review Notes` section. Any unchecked item → the Architect Review row is ❌ regardless of automated check status.

### 6. Produce the report

Output in this exact format:

```
## Phase Gate Report — PHASE_[XX]

| Check              | Status | Details                                     |
|--------------------|--------|---------------------------------------------|
| Infrastructure     | ✅/❌  |                                             |
| Backend tests      | ✅/❌  | N passed, M failed                          |
| Type generation    | ✅/❌  |                                             |
| Frontend typecheck | ✅/❌  | N errors                                    |
| Frontend unit      | ✅/❌  | N passed, M failed                          |
| E2E                | ✅/❌  | N passed, M failed — report: [path]         |
| Smoke              | ✅/❌  | HTTP NNN                                    |
| Architect review   | ✅/❌  | no open items / N unchecked                 |

**Overall: ✅ PASS / ❌ FAIL**
```

If Architect Review is ❌, list each unchecked item verbatim under an `Open architect review notes` heading.

On **PASS**: confirm it is safe to commit with the atomic commit message from the phase file.

On **FAIL**: list each failed check with specific error output. Also list unchecked architect review notes if any remain. Do NOT suggest committing. Suggest fixes where obvious.

## Rules

- Do not edit any code files — this workflow is read-only.
- Do not commit.
- Do not run destructive commands (e.g. `docker compose down`).
- Do not stop at the first failure — run every check.
- Do not auto-start the full app stack just to make the e2e check pass.
- Do not return PASS while any architect review checklist item remains unchecked.

## Done when

- Every required check has a reported status.
- The output clearly says PASS or FAIL.
- Any unchecked architect review notes are listed explicitly in the report.
