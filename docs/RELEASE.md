# Release Playbook

This repository ships two independently versioned components:

- **Workflow release** — the reusable `workflow/` + `sdd` CLI surface, tagged as `workflow/vX.Y.Z`. Version lives in `pyproject.toml` `project.version`.
- **Template release** — each shipped stack under `templates/<template-id>/`, tagged as `template/<template-id>/vX.Y.Z`. Version lives in `templates/<template-id>/template.yaml` `version`.

Generated projects resolve upgrade targets by checking out these tags and reading the archived content through `git archive`. Tags are the contract — they must exist and must match the versions recorded in the workspace.

## Namespaced tag layout

```text
workflow/v0.1.0
workflow/v0.2.0
template/fastapi-nuxt/v0.1.0
template/fastapi-nuxt/v0.2.0
template/fastapi-react-router/v0.1.0
```

Workflow and template versions advance independently. A single commit on `main` can host the release commit for the workflow, any subset of templates, or all of them.

## Pre-release checklist

Run from a clean `main` checkout:

1. **Bump versions** in the same commit that should become the release.
   - Workflow release: edit `pyproject.toml` `project.version`.
   - Template release: edit `templates/<template-id>/template.yaml` `version`.
   - Adjust only the components you are actually releasing.

2. **Validate structure against the new (not-yet-published) tags.** This must succeed before tagging:

   ```bash
   uv run sdd release validate --scope workflow --template fastapi-nuxt --expect-new-tags
   uv run sdd release validate --scope template --template fastapi-nuxt --expect-new-tags
   uv run sdd release validate --scope template --template fastapi-react-router --expect-new-tags
   ```

   `--expect-new-tags` fails fast if the tag you are about to cut already exists.

3. **Confirm coordinates with `release status`** before running any `git tag`:

   ```bash
   uv run sdd release status --template fastapi-nuxt
   uv run sdd release status --template fastapi-react-router
   ```

   Check the `expected_tag`, `expected_tag_exists: false`, and `latest_tag` fields.

## Publishing tags

Once validation is green, tag the release commit and push the tags:

```bash
git tag workflow/vX.Y.Z
git tag template/fastapi-nuxt/vX.Y.Z
git tag template/fastapi-react-router/vX.Y.Z

git push origin workflow/vX.Y.Z
git push origin template/fastapi-nuxt/vX.Y.Z
git push origin template/fastapi-react-router/vX.Y.Z
```

Release only the components whose versions changed in the release commit. Do not retag a component that was not bumped.

## Post-release validation

After the tags are pushed, confirm generated projects will see a consistent release surface:

```bash
uv run sdd release validate --scope all --template fastapi-nuxt --expect-existing-tags
uv run sdd release validate --scope all --template fastapi-react-router --expect-existing-tags
```

`--expect-existing-tags` fails if any expected tag is missing, which makes partial publishes visible.

The CI `Release E2E` job exercises the full resolution path (`sdd release status`, `sdd release validate --expect-existing-tags`, `sdd upgrade --check`, `sdd upgrade --apply`) against an ephemeral git repo that creates real namespaced tags. A green `Release E2E` on `main` means the released-artifact code path still works; it does not imply any specific release has been cut.

## Rolling back

`git tag -d <tag>` removes a local tag. `git push origin :refs/tags/<tag>` removes the published tag. Do both before re-tagging the same version, and prefer bumping to a new patch version over reusing an already-published tag — generated projects pin to concrete tags and will not automatically notice force-moved tags.

## Non-goals

- This playbook does not automate the `git tag` step. Cutting tags is a deliberate maintainer action that should happen only when the pre-release checklist is green.
- `dev/` is never part of a release. Only `workflow/` and `templates/<id>/` content is reachable via tagged `git archive` extractions.
