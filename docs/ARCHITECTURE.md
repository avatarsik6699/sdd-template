# Architecture

> Template memory file for derived projects.
> Keep this document short and high-signal. Update it when the system shape changes.

## System Overview

- Product: `[PROJECT_NAME]`
- Primary goal: `[one-paragraph description of what the system does]`
- Main user flows:
  - `[flow 1]`
  - `[flow 2]`
  - `[flow 3]`

## Top-Level Shape

- Frontend: `[framework, app entrypoints, key UI areas]`
- Backend: `[framework, API boundaries, workers, background jobs]`
- Data: `[primary database, caches, queues, object storage]`
- Integrations: `[payments, auth provider, email, analytics, etc.]`

## Module Boundaries

| Area | Responsibility | Notes |
|------|----------------|-------|
| `[frontend/app]` | `[what it owns]` | `[constraints]` |
| `[backend/api]` | `[what it owns]` | `[constraints]` |
| `[shared/types]` | `[what it owns]` | `[constraints]` |

## Request / Data Flow

1. `[user action or external trigger]`
2. `[frontend or client behavior]`
3. `[backend / worker behavior]`
4. `[database / side effect / outbound integration]`

## Cross-Cutting Rules

- Authentication: `[how auth works]`
- Authorization: `[role / permission model]`
- Validation: `[where input validation happens]`
- Observability: `[logs, metrics, tracing]`
- Error handling: `[error contract / retries / alerts]`

## Change Triggers

Update this file when any of the following changes:
- a new major subsystem or service is added
- responsibilities move between modules
- request or event flows change materially
- authentication, authorization, or deployment topology changes
