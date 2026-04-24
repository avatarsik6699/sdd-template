---
name: template-repo-maintainer
description: Use when working inside the sdd-template repository itself to change workflow assets, template assets, or the sdd CLI. This skill keeps maintainer work on authoritative sources, avoids derived-project-only phase skills, and uses sdd validation commands to test workflow/template changes safely.
---

# Template Repo Maintainer

This skill is for maintaining the `sdd-template` repository itself.

Use it when the task changes:

- `workflow/`
- `templates/`
- `workflow/cli/`
- repo-maintainer docs such as `README.md`, `AGENTS.md`, `CLAUDE.md`, or `docs/TEMPLATE_AUTHORING.md`

Do not use it inside generated projects.

## First checks

1. Read `AGENTS.md`.
2. Confirm the task improves the template for future projects, not one derived project.
3. Identify the authoritative owner before editing anything.

## Authoritative owner map

- Workflow behavior:
  - `workflow/docs/playbooks/`
  - `workflow/project-files/`
  - `workflow/cli/`
- Template-specific stack behavior:
  - `templates/<template-id>/template.yaml`
  - `templates/<template-id>/source/`
- Maintainer guidance:
  - `README.md`
  - `AGENTS.md`
  - `CLAUDE.md`
  - `docs/TEMPLATE_AUTHORING.md`

Never treat `dev/` as canonical. It is a disposable integration lab.

## Do not use derived-project-only skills here

Do not run:

- `/phase-init`
- `/phase-gate`
- `/spec-sync`
- `/context-update`

Those are shipped to generated projects. If you need to validate them, generate a scratch project first.

## Preferred maintainer workflow

1. Make the change in the authoritative source.
2. If template structure changed, validate the template:

   ```bash
   uv run sdd register-template templates/<template-id>
   uv run sdd release validate --scope template --template <template-id> --skip-tag-checks
   ```

3. If workflow/project composition changed, generate a scratch project:

   ```bash
   uv run sdd init --template <template-id> --project-name demo-project ./tmp/demo-project
   uv run sdd integrate --check ./tmp/demo-project
   uv run sdd gate resolve ./tmp/demo-project
   uv run sdd upgrade --check ./tmp/demo-project
   ```

4. If you used `dev/`, treat it as diagnostic only:

   ```bash
   uv run sdd dev rebuild --template <template-id>
   uv run sdd dev diff --template <template-id>
   uv run sdd dev promote --template <template-id>
   ```

   `sdd dev promote` is for classification and guarded reverse-sync review, not blind promotion.

5. Update maintainer docs when structure or commands changed.
6. Run focused tests for the touched area.

## Guardrails

- Do not reintroduce root-level product-stack files.
- Do not edit generated files when the source template or workflow file is available.
- Do not hide integration logic in AI-only instructions when it belongs in `sdd`.
- Keep skills thin and CLI-first.
- Prefer template-agnostic wording in maintainer docs unless a template-specific example is required.

## Done when

- changes live in authoritative sources
- `README.md` / `AGENTS.md` / `CLAUDE.md` stay consistent
- relevant `sdd` commands and focused tests pass
- no new compatibility shadow copy becomes the source of truth
