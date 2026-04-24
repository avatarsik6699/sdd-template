# FastAPI + React Router SSR

Second reference template used to prove the `workflow + templates + sdd` split against a stack
that is not Nuxt-based.

This template keeps the FastAPI backend and Docker workflow from the first reference stack, but
swaps the frontend to React 19 + React Router framework mode with SSR and route-level SEO metadata.

Canonical source lives under [source/](source/). Validate this template with:

```bash
uv run sdd release validate --scope template --template fastapi-react-router --skip-tag-checks
uv run sdd init --template fastapi-react-router --project-name demo-project ./tmp/demo-project
```
