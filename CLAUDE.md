# Rules of operation of the AI agent during [PROJECT_NAME] development

1. **Scope Lock**: Do only what is specified in the active `docs/PHASE_XX.md`. Do not assume the realization of future phases.
2. **No Guessing**: If the requirement is ambiguous → ask a question in the terminal. Don't write code "to suit your taste".
3. **Gates First**: Before each commit, run `/phase-gate N`. Commit only if the gate report is ✅ PASS.
4. **Atomic Commits**: The format is `feat|fix|chore|docs|test|refactor(scope): description`. 1 commit = 1 logical task.
5. **Security**: No hardcodes, no secrets in the code. Use `.env`, `os.getenv()`, `Pydantic Settings`.
6. **Output**: First, the plan → waiting `✅` → code → tests → commit. Don't skip the steps.
7. **Context**: After completing each phase, run `/context-update N` to update `docs/CONTEXT.md`, `docs/STATE.md`, and `docs/CHANGELOG.md`.

---

## Git Workflow Rules

8. **Branch Rule**: Work only in `feat/phase-N` branches. Never push directly to `main` or `develop`.
   ```bash
   git checkout -b feat/phase-01
   ```

9. **No Destructive Git**: Never use `--force`, `git push --force`, `git rebase` on shared branches (`main`, `develop`), or `git reset --hard` without explicit user instruction.

10. **Conventional Commits**: Every commit follows `type(scope): description`.
    - Types: `feat`, `fix`, `chore`, `docs`, `test`, `refactor`
    - Example: `feat(phase-01): foundation — docker, db, jwt auth, nuxt skeleton`

11. **Gate Before Commit**: Run `/phase-gate N` first. Never commit if gate report shows ❌ FAIL.

12. **Tagging**: After a phase branch merges to `develop`:
    ```bash
    git tag -a v0.N.0 -m "Phase N: [title]"
    ```

---

## Spec Change Sync Protocol

When `docs/SPEC.md` is modified:

1. **Run immediately**: `/spec-sync [brief description of what changed]`
2. The skill will automatically:
   - Add an entry to `docs/CHANGELOG.md`
   - Increment `docs/CONTEXT.md` `_meta.version` if DB/API/types changed
   - Mark affected phases as `⚠️ NEEDS_REVIEW` in `docs/STATE.md`
   - Add warning notices to affected `docs/PHASE_XX.md` files
3. **Review** all changes before committing
4. **Do not implement** any phase marked `⚠️ NEEDS_REVIEW` until the review is resolved

---

## CONTEXT.md Version Rules

- **Format**: `vMAJOR.MINOR` (e.g., `v1.2`)
- **Patch bump** (`v1.0` → `v1.1`): additive changes — new endpoints, models, env vars
- **Minor bump** (`v1.1` → `v1.2`): breaking changes — renamed/removed endpoints, schema changes, type changes
- **No bump**: documentation-only phase, zero contract changes
- Always update `captured_at` date when version changes
- `CONTEXT.md` is the Single Source of Truth for AI — never let it fall more than one phase behind

---

## Skills Reference

| Command | When to use |
|---------|-------------|
| `/spec-sync [description]` | Immediately after modifying `docs/SPEC.md` |
| `/phase-gate [N]` | Before committing phase work |
| `/context-update [N]` | After phase gate passes |
| `/phase-init [N]` | To scaffold the next phase document |
| `/my-review [file]` | Code review of specific files |

---

## Phase Lifecycle

```
1.  Architect fills docs/SPEC.md
2.  /phase-init N       → creates docs/PHASE_N.md scaffold
3.  Architect fills Contracts + Files sections in PHASE_N.md
4.  AI implements scope (on feat/phase-N branch)
5.  /phase-gate N       → all checks green (✅ PASS)
6.  git commit          → feat(phase-N): [description]
7.  /context-update N   → updates CONTEXT.md, STATE.md, CHANGELOG.md
8.  PR to develop       → human review → merge
9.  git tag -a v0.N.0 -m "Phase N: [title]"
10. /phase-init N+1     → repeat
```

---

## Document Roles

| File | Role | Changes |
|------|------|---------|
| `docs/SPEC.md` | Strategic brief: goals, roles, domain rules, non-functional reqs | Rarely — architect only |
| `docs/CONTEXT.md` | Living technical contract: DB schema, endpoints, TS types, env vars | After each phase via `/context-update` |
| `docs/STATE.md` | Operational tracker: phase statuses, blockers, feedback | Continuously |
| `docs/CHANGELOG.md` | History of spec/architecture changes | On every SPEC.md or CONTEXT.md change |
| `docs/PHASE_XX.md` | Mini-spec for AI: scope, files, contracts, gate checks | Created per phase via `/phase-init` |
| `docs/PHASE_TEMPLATE.md` | Template for new phases | Only when improving the template itself |
