# Rules of operation of the AI agent during [PROJECT_NAME] development

1. **Scope Lock**: Do only what is specified in the active `docs/PHASE_XX.md`. Do not assume the realization of future phases.
2. **No Guessing**: If the requirement is ambiguous → ask a question in the terminal. Don't write code "to suit your taste".
3. **Gates First**: Before each commit, run: `pytest`, `vitest`, `tsc --noEmit`, `docker compose up -d`. Commit only if all are green.
4. **Atomic Commits**: The format is `feat|fix|chore|docs(scope): description`. 1 commit = 1 logical task.
5. **Security**: No hardcodes, no secrets in the code. Use `.env`, `os.getenv()`, `Pydantic Settings`.
6. **Output**: First, the plan → waiting `✅` → code → tests → commit. Don't skip the steps.
7. **Context**: After completing each phase, update `docs/CONTEXT.md` and `docs/STATE.md` before moving on.
