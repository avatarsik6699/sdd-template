# Known Gotchas

> Template memory file for derived projects.
> Capture recurring pitfalls that repeatedly waste time during coding, testing, or deploys.

## How To Use

- Add only issues that are likely to happen again.
- Prefer concrete symptoms, root cause, and the shortest reliable fix.
- Remove entries that are no longer relevant.

## Gotcha Log

### Docker-owned files break host operations (`EACCES` / `EPERM` / read-only)

- **Symptoms**: file operations fail with `EACCES`, `EPERM`, "Permission denied", or "Read-only file system". Most common paths: `frontend/.nuxt/`, `frontend/.output/`, `node_modules/.cache/`, `__pycache__/`.
- **Root cause**: a Docker container wrote to a bind-mounted host directory as root.
- **Fix (host)**:
  ```bash
  sudo chown -R $USER:$USER <path>   # reclaim ownership, keep files
  sudo rm -rf <path>                 # OR discard the generated artefact
  ```
- **Agent protocol**: agents MUST NOT run `sudo`, `chmod -R 777`, or loop the failing operation. Instead, stop and post this exact handoff to the user (substituting real `<path>` and `<cmd>`):

  > ⛔ **Permission denied.** I cannot modify `<path>` while running `<cmd>`.
  >
  > This usually happens when a Docker container wrote files to a bind-mounted host directory as root. Please run one of the following on the host:
  >
  > ```bash
  > sudo chown -R $USER:$USER <path>
  > sudo rm -rf <path>
  > ```
  >
  > When the fix is applied, reply with the single word **`continue`** and I will retry the failed operation from the same step.

  On receiving `continue` (case-insensitive), retry the failed operation once. If it fails a second time with the same error, stop again and ask the user to confirm the fix was actually applied — do not loop a third time.

- **Prevention**: run Docker with a matching host UID/GID or use named volumes for cache directories that containers own.

### Redis ships without auth — wire `--requirepass` end-to-end if you need it

- **Symptoms**: App connects fine to Redis in dev, but a security review flags an unauthenticated cache. Or: auth was added in one place (e.g. `--requirepass` on the container) but the app still connects, only because `REDIS_URL` was never updated to include the password.
- **Root cause**: The template's default `redis` service has no password and `REDIS_URL=redis://redis:6379/0` reflects that. Adding auth requires changes in three places or the healthcheck silently fails.
- **Fix**: If the derived project needs auth'd Redis:
  1. Add `REDIS_PASSWORD=<secret>` to `.env.example` and generate it in `scripts/init-project.sh` / `scripts/setup-prod.sh`.
  2. In `docker-compose.yml`, set `command: redis-server --requirepass ${REDIS_PASSWORD}` and update the healthcheck to `redis-cli -a ${REDIS_PASSWORD} ping`.
  3. Change `REDIS_URL` to `redis://:${REDIS_PASSWORD}@redis:6379/0`.
- **Prevention**: flip all three together in a single commit and verify `docker compose exec redis redis-cli ping` returns `NOAUTH` before auth, `PONG` after.
- **Links**: https://redis.io/docs/latest/operate/oss_and_stack/management/security/

### `[short problem title]`

- Symptoms: `[what you usually see]`
- Root cause: `[why it happens]`
- Fix: `[the shortest safe resolution]`
- Prevention: `[what to check next time]`
- Links: `[relevant docs / issue / PR]`
