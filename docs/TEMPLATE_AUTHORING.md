# Template Authoring

This repository is a template-authoring workspace. New stacks belong under
`templates/<template-id>/`, and the canonical bootstrap path for manifest
generation is `sdd register-template`.

## Minimal authoring loop

1. Create the stack directory:
   - `templates/<template-id>/source/` for stack files
   - `templates/<template-id>/README.md` for maintainer-facing notes

2. Add the stack assets you actually want to ship:
   - backend/frontend code
   - stack-local docs
   - helper scripts
   - CI/deploy files

3. Generate a draft manifest:

   ```bash
   uv run sdd register-template templates/<template-id> --write
   ```

4. Review `templates/<template-id>/template.yaml`:
   - confirm `template_id`, `display_name`, and `version`
   - confirm inferred `package_managers`
   - remove or adjust any incorrect `technologies`
   - confirm `init_hooks`, `gate`, and `smoke`

5. Validate the template structure:

   ```bash
   uv run sdd release validate --scope template --template <template-id> --skip-tag-checks
   ```

6. Test composition:

   ```bash
   uv run sdd init --template <template-id> --project-name demo-project ./tmp/demo-project
   uv run sdd gate resolve ./tmp/demo-project
   ```

7. If you are using an AI agent to maintain this repository, load the repo-only maintainer skill:
   [`.codex/skills/template-repo-maintainer/SKILL.md`](.codex/skills/template-repo-maintainer/SKILL.md).
   It is specifically for template-repo work and keeps the agent on authoritative sources.

## What `sdd register-template` infers

- `source_dir`
- `package_managers`
- common technologies from Python/frontend stack markers
- `init_hooks` from obvious init scripts
- `gate.helper_script`
- `gate.stack_docs`
- `smoke.docs_anchor`

It is intentionally conservative. Review ambiguous fields manually instead of
expecting the CLI to guess stack semantics perfectly.

## When to add adapter scripts

Prefer manifest fields first. Add adapter/helper scripts only when the stack
cannot be described cleanly with:

- `package_managers`
- `init_hooks`
- `gate`
- `smoke`

If you add scripts, declare them explicitly in `template.yaml` and keep them in
the template-owned `source/` tree.
