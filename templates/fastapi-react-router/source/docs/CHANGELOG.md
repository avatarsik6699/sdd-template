# CHANGELOG — Spec & Architecture History

> Records changes to `docs/SPEC.md` and `docs/CONTEXT.md`. This is **NOT** a git commit log.
> Purpose: capture *why* the contract changed and which phases were affected.
> Format: newest entry at top.

---

## v0.1.0 — 2026-04-24 — First Published Template Release

**Type**: addendum
**Author**: template-maintainer
**Triggered by**: Template repository release cut for namespaced workflow/template tags

### Changes
- Published template release coordinate: `template/fastapi-react-router/v0.1.0`
- Published compatible workflow coordinate: `workflow/v0.1.0`
- Added released-artifact validation/status flow for maintainers
- Hardened upgrade baseline integrity by ignoring local `.claude/settings.local.json`

### Affected Phases
- None (template maintainer release surface)

### Contract Updates
- No SPEC/CONTEXT schema change; release metadata and upgrade behavior hardened

### Notes
- This entry documents template release readiness for generated projects based on tagged artifacts.

---

## v1.0 — [DATE] — Initial Template

**Type**: initial-setup
**Author**: [OWNER]
**Triggered by**: Project initialization from sdd-template

### Changes
- `SPEC.md` created: project goals, roles, data model, API endpoints, phase plan
- `CONTEXT.md` v1.0 created: initial stack snapshot, core models, active endpoints
- `PHASE_01.md` created: Foundation scope defined

### Affected Phases
- None (initial state)

### Contract Updates
- `CONTEXT.md` initialized at `v1.0`

---

<!--
ENTRY TEMPLATE — copy this block when adding a new entry:

## [CONTEXT_VERSION] — [YYYY-MM-DD] — [Short Title]

**Type**: spec-change | arch-decision | breaking-change | phase-completion | addendum
**Author**: [name / AI skill]
**Triggered by**: [What caused this? User request, bug discovery, new requirement, etc.]

### Changes
- [bullet: what specifically changed in SPEC.md or the architecture]

### Affected Phases
- PHASE_XX — [why it is affected]

### Contract Updates
- `CONTEXT.md` bumped from `vX.Y` to `vX.Z`
- [list schema / endpoint / type changes]

### Notes
[Trade-offs, decisions, context not captured elsewhere]

-->
