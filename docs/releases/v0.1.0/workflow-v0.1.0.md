## workflow/v0.1.0

First published workflow release for namespaced component tags.

### Highlights
- Introduces namespaced workflow release coordinate: `workflow/v0.1.0`.
- Provides maintainer release status/validation flow (`sdd release status`, `sdd release validate`).
- Supports released-artifact upgrade checks against tagged baselines.
- Includes baseline integrity hardening to ignore local `.claude/settings.local.json` drift.

### Compatibility
- Designed to work with template releases:
  - `template/fastapi-nuxt/v0.1.0`
  - `template/fastapi-react-router/v0.1.0`
