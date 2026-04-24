# Workflow / Template Split Refactoring Plan

> Working plan for separating the reusable SDD workflow from concrete technology stacks inside the `sdd-template` repository.
>
> Status: implementation complete
> Last updated: 2026-04-24

---

## 1. Goal

The repository should stop behaving like one mixed package that contains:

- one reusable development workflow
- one specific FastAPI/Nuxt reference stack
- one set of runtime wrappers and bootstrap scripts

and should instead behave like:

- one reusable **workflow**
- one or more selectable **templates**
- one deterministic **CLI** that integrates workflow + template into a generated project
- one thin AI **skill** layer that drives the CLI

The main simplification is this:

- template authors should build a stack
- maintainers should provide automation that inspects, integrates, and validates it
- users should run one clear entrypoint instead of manually understanding internal boundaries

### 1.1 Current implementation snapshot

The repository has already completed the first major cleanup slices:

- `workflow/` is the canonical home for reusable workflow playbooks, project files, and the `sdd` CLI
- `templates/fastapi-nuxt/` is the canonical home for the reference stack and its shipped runtime assets
- `human-instructions/` has been removed
- `docs/workflows/` has been removed
- the repository root is no longer a runnable copy of the reference stack

What remains is the deeper productization work:

- release publishing discipline around namespaced workflow/template tags
- broader multi-template parity and validation depth across shipped stacks
- ongoing hardening of maintainer automation and guidance

---

## 2. Terminology to use from now on

These names are settled for this refactor:

- **workflow**: the reusable SDD process, playbooks, rules, runtime wrappers, and bootstrap/integration tooling
- **template**: a concrete technology stack or project preset
- **reference template**: the current in-repo FastAPI/Nuxt stack used to validate the workflow end-to-end
- **integration manifest**: machine-readable metadata used by tooling to wire a template into the workflow
- **CLI**: the canonical executable integration tool
- **skill**: a thin AI runtime wrapper that calls the CLI and explains or completes ambiguous steps

Names we should stop using for this design:

- `core` as the primary architectural term
- `human-instructions/` as a permanent location for canonical shipped files

---

## 3. Design principles

1. User experience should be simple even if internal implementation is structured.
2. The CLI is the source of truth for initialization and integration behavior.
3. Skills must stay thin; they orchestrate the CLI rather than reimplement it.
4. Templates may be tightly coupled to the workflow after generation.
5. The repository still needs explicit machine-readable metadata, even if authors do not write most of it by hand.
6. Template authors should create stacks, not hand-maintain large contract documents.
7. Any metadata that can be inferred should be generated automatically and only reviewed when ambiguous.

---

## 4. What was wrong before the refactor

### 4.1 Structural problems

- the repository root looked like one concrete full-stack product template
- bootstrap and gate helpers lived at the root as if they were universally canonical
- `docs/STACK.md` carried too much global responsibility
- root docs blurred reusable workflow behavior and reference-stack behavior

### 4.2 Naming problems

- `core` is overloaded and semantically weak for this repository
- `human-instructions/` does not describe what the directory actually contains

### 4.3 Automation problems

- initialization logic is hardcoded instead of driven by a reusable CLI model
- stack assumptions are mostly implicit in scripts and repo layout
- current integration behavior is difficult to explain because the wiring is scattered across docs and shell scripts

---

## 5. Findings about `human-instructions/`

This section is retained as migration history. The directory no longer exists in the repository.

Former contents:

- `human-instructions/AGENTS.for-new-projects.md`
- `human-instructions/CLAUDE.for-new-projects.md`
- `human-instructions/how_to_create_skills.md`
- `human-instructions/vs_code_settings_up.md`

### 5.1 Files that are actually part of the workflow pipeline

- `AGENTS.for-new-projects.md`
- `CLAUDE.for-new-projects.md`

Those two files were used by the bootstrap flow to generate derived-project `AGENTS.md` and `CLAUDE.md`.

### 5.2 Files that are not part of the workflow pipeline

- `how_to_create_skills.md`
- `vs_code_settings_up.md`

Current findings:

- no active workflow wrapper points at them
- they are not part of the bootstrap contract
- they are generic notes, not canonical workflow assets
- they are dead weight inside `human-instructions/` as currently positioned

### 5.3 Decision

The `human-instructions/` directory had to be removed.

Implemented replacement:

- move derived-project canonical files into a semantically correct workflow-owned location
- delete non-pipeline notes that are outside the maintained workflow asset set

Implemented destination:

```text
workflow/
  project-files/
    AGENTS.md.template
    CLAUDE.md.template
```

Decision for the two note files:

- delete `human-instructions/how_to_create_skills.md`
- delete `human-instructions/vs_code_settings_up.md`
- do not relocate them into the new workflow structure

---

## 6. Target architecture

### 6.1 Repository model

The repository should be understood as these parts:

1. **workflow/**
   - workflow playbooks
   - generated-project canonical files
   - runtime adapters for Claude/Codex
   - CLI implementation
   - integration logic and validation rules

2. **templates/**
   - concrete stack templates
   - each template may use any language, package manager, repo shape, and architecture

3. **dev/**
   - workspace used to validate workflow + selected template together during development

4. **docs/**
   - repo-maintainer documentation
   - architecture notes
   - migration plans

5. **generated projects**
   - independent repositories created from `workflow/` + a selected template
   - retain provenance and ownership metadata so they can receive controlled upstream updates
   - use explicit upgrade commands instead of ad hoc regeneration

### 6.2 Canonical workflow playbook location

This migration decision is now complete:

- canonical workflow playbooks should live under `workflow/docs/playbooks/`
- runtime wrappers should point to `workflow/docs/playbooks/`, not to duplicated copies
- `docs/workflows/` has been removed

### 6.3 Current target tree

```text
.
├── workflow/
│   ├── docs/
│   │   └── playbooks/
│   ├── project-files/
│   │   ├── AGENTS.md.template
│   │   └── CLAUDE.md.template
│   ├── cli/
│   └── __init__.py
├── templates/
│   ├── fastapi-nuxt/
│   │   ├── source/
│   │   ├── template.yaml
│   │   └── README.md
│   └── ...
├── docs/
│   └── REFACTOR_CORE_TEMPLATE_SPLIT_PLAN.md
├── tests/
└── README.md
```

`dev/` is intentionally omitted from the tree above because it is generated on demand and should not
be retained as a stable authored directory in the repository.

### 6.4 Authoritative-source rule

This rule should govern the repository at all times:

- `workflow/` and `templates/` are the only authoritative sources
- `dev/` is a generated integration lab
- changes discovered in `dev/` must be promoted back into authoritative sources before they are considered real

`dev/` should therefore be treated as:

- reproducible
- disposable
- useful for validation
- unsafe as a long-lived source of truth

This rule is especially important because it simplifies both human and AI behavior.

---

## 7. Integration model: CLI first, skill second

This is the key architecture decision.

### 7.1 Canonical behavior lives in the CLI

The workflow should not rely on a skill as the primary implementation of integration logic.

The canonical interface should be something like:

```bash
sdd init --template fastapi-nuxt --project-name my-project
sdd register-template templates/fastapi-nuxt
sdd integrate --template fastapi-nuxt
```

Why:

- deterministic behavior
- testable outside AI runtimes
- usable in CI and local shells
- one implementation instead of duplicating behavior across Claude/Codex/manual usage

### 7.2 The skill remains valuable

The skill should:

- call the CLI
- explain what the CLI is doing
- help resolve ambiguous detections
- surface validation failures clearly
- guide maintainers through authoring or migration tasks

The skill should not:

- become the only place where integration logic exists
- maintain its own copy of wiring rules

---

## 8. Integration metadata: generated manifest, not hand-written contract

The repository still needs machine-readable template metadata. The difference is how it is produced.

### 8.1 What we are not doing

- we are not asking maintainers to hand-author a large abstract contract document before they can use a template

### 8.2 What we are doing

- the CLI analyzes and registers a template
- the CLI generates a draft integration manifest
- the maintainer reviews only uncertain fields
- the CLI uses that manifest during integration and validation

### 8.3 Minimal manifest responsibilities

Each template should ultimately expose a small manifest, for example `template.yaml`, with fields such as:

- template id
- manifest schema version
- display name
- version
- technologies
- package manager detection
- init hooks
- gate command groups
- smoke check command or probe
- optional dev-start command
- placeholder replacement rules
- optional adapter scripts for nontrivial setup

The important point:

- this metadata exists for tooling
- template authors should not need to design it from scratch manually

### 8.4 Manifest schema compatibility

The integration manifest must be versioned explicitly.

Rules:

- every `template.yaml` must declare a `manifest_schema_version`
- the CLI must support a clearly documented compatibility window for older manifest versions
- if a manifest version is unsupported, the CLI must fail with a migration message instead of guessing
- manifest schema upgrades should be explicit and reviewable

### 8.5 Template hooks and adapter trust model

Templates may need `init hooks` or adapter scripts, but the CLI must treat executable template logic as a controlled surface.

Rules:

- hooks and adapter scripts must be declared explicitly in `template.yaml`
- undeclared executable steps must not run implicitly
- trusted in-repo templates may execute declared hooks by default
- non-local or externally sourced templates must require explicit user confirmation before running hooks
- `sdd init --check`, `sdd integrate --check`, and equivalent dry-run/reporting modes must list all hooks that would run
- hook execution logs should be recorded clearly so failures are diagnosable

Design goal:

- templates may extend the system when needed
- executable behavior must remain explicit, reviewable, and bounded

---

## 9. CLI responsibilities

The initial CLI surface should be small and focused.

### 9.1 `sdd init`

Responsibilities:

- choose a template
- copy workflow files into the target project
- copy the chosen template into the target project
- prepare the project for integration

### 9.2 `sdd register-template`

Responsibilities:

- analyze a template directory
- detect likely commands, layout, package managers, and entrypoints
- generate a draft `template.yaml`
- flag ambiguous fields for human review

### 9.3 `sdd integrate`

Responsibilities:

- wire the workflow into the selected template
- apply placeholders and generated project naming
- install or generate runtime wrappers
- configure workflow-facing stack commands
- validate that integration is coherent

### 9.4 Optional later commands

- `sdd validate-template`
- `sdd list-templates`
- `sdd doctor`
- `sdd upgrade`
- `sdd upgrade --check`

### 9.5 Maintainer dev commands

To support development of the template repository itself, the CLI should also expose a maintainer-oriented `dev` group.

Initial command set:

- `sdd dev rebuild --template <name>`
- `sdd dev run --template <name>`
- `sdd dev diff --template <name>`
- `sdd dev promote --template <name>`
- `sdd dev clean --template <name>`

Command intent:

- `rebuild`: regenerate `dev/<template>/` from authoritative sources
- `run`: start or exercise the generated dev workspace
- `diff`: compare the generated dev workspace against what authoritative sources would produce
- `promote`: assist with reverse-mapping exceptional `dev/` edits back into `workflow/` or `templates/`
- `clean`: remove generated dev state safely

Important rule:

- `sdd dev promote` is an exception-handling tool, not the primary development flow

### 9.6 Downstream project upgrade commands

Generated projects need an explicit upgrade path that is separate from maintainer-side `dev/` workflows.

Initial command set:

- `sdd upgrade --check`
- `sdd upgrade workflow`
- `sdd upgrade template`
- `sdd upgrade --to workflow@<version>`
- `sdd upgrade --to template@<template-id>@<version>`

Command intent:

- `--check`: compute and display an upgrade plan without modifying files
- `workflow`: upgrade workflow-managed assets only
- `template`: upgrade template-managed assets only
- `--to ...`: target an explicit workflow or template version

Important rule:

- downstream upgrades must never behave like blind project regeneration

### 9.7 Release and distribution model

The upgrade mechanism needs one clear source of truth for published workflow/template versions.

Decision:

- workflow and template releases should be published from this repository through Git tags and GitHub releases
- the `sdd` CLI may also be distributed as an installable package, but release metadata must still resolve back to repository tags/releases
- generated projects should record workflow/template versions as immutable release identifiers, not branch names

Release rules:

- `workflow@<version>` resolves to a published workflow release artifact derived from a tagged repository state
- `template@<template-id>@<version>` resolves to a published template artifact derived from a tagged repository state
- release artifacts must be reproducible from the tagged source tree
- upgrades must target released versions by default; raw branch-based upgrades are a maintainer/debugging path only

Version naming rules:

- workflow releases should use namespaced tags like `workflow/v1.2.0`
- template releases should use namespaced tags like `template/<template-id>/v2.3.0`
- workflow and templates should therefore have independent version streams
- repository-level releases may still exist for human communication, but CLI upgrade resolution must use the namespaced component tags above

Why this model:

- Git tags and releases are simple, standard, and inspectable
- they avoid inventing a custom distribution registry too early
- they provide stable upgrade coordinates for downstream projects

---

## 10. Maintainer development loop for this repository

This section defines how maintainers should evolve the template repository itself.

### 10.1 Normal development loop

The preferred loop is:

1. edit authoritative files in `workflow/` or `templates/<name>/`
2. run `sdd dev rebuild --template <name>`
3. validate behavior inside `dev/<name>/`
4. if the workflow or template still feels wrong, go back to authoritative sources
5. rebuild `dev/` again until the generated workspace behaves correctly

This means the canonical loop is:

- edit authoritative source
- regenerate dev workspace
- validate
- repeat

It is explicitly not:

- edit inside `dev/`
- keep `dev/` as a parallel source of truth
- try to synchronize two authoritative copies of the system

### 10.2 Exceptional loop for debugging in `dev/`

Sometimes a maintainer or AI agent will test a quick fix directly inside `dev/` because it is faster during debugging.

That is allowed only as a short-lived exploratory step.

Required recovery flow:

1. inspect the change with `sdd dev diff --template <name>`
2. classify the change as:
   - workflow-owned
   - template-owned
   - generated noise that must not be promoted
3. use `sdd dev promote --template <name>` only to assist with mapping
4. re-apply the approved change in `workflow/` or `templates/<name>/`
5. rebuild `dev/` from authoritative sources
6. verify that the temporary `dev/` diff disappears

### 10.3 Re-entry and recovery behavior for `sdd init` and `sdd integrate`

The CLI must behave predictably if initialization or integration is retried.

Rules:

- `sdd init` should refuse to write into a non-empty target directory unless the user explicitly opts into a supported recovery or overwrite mode
- `sdd integrate` should be designed to be idempotent for already-integrated projects where managed files and metadata are present
- if integration detects partial prior state, it should enter an explicit repair mode instead of silently continuing
- repair mode should verify metadata, re-materialize missing managed files, and re-run only the missing or invalid integration steps
- if the project state is too inconsistent to repair safely, the CLI must stop with a concrete report instead of guessing

### 10.4 Commit policy

Maintainers should commit:

- `workflow/`
- `templates/`
- runtime wrappers
- docs
- CLI and integration logic

Maintainers should not commit long-lived hand edits from generated `dev/` workspaces as if they were canonical sources.

If `dev/` needs to be committed at all, it should be only for clearly defined generated fixtures with a documented reason.

### 10.5 Why this model is preferred

This approach is better than a bidirectional-sync model because it:

- preserves one source of truth
- keeps code review understandable
- keeps CI easier to reason about
- makes regeneration a normal operation
- avoids hidden drift between sandbox and canonical source

---

## 11. AI-agent safety rules for maintainer work

The repository should assume that maintainers will often work through AI agents. That means the workflow must defend against a common failure mode:

- the user asks to improve the template system
- the agent makes changes directly inside `dev/`
- the sandbox accidentally becomes the de facto implementation surface

That failure mode should be prevented explicitly.

### 11.1 Repository rule for agents

When the task is to improve the template repository itself:

- agents must treat `workflow/` and `templates/` as authoritative
- agents must treat `dev/` as generated and non-authoritative
- agents must not make durable implementation changes in `dev/` unless the task is explicitly marked as exploratory debugging

### 11.2 Required guardrails

We should add one or more of the following protections:

1. **AGENTS.md rule**
   Add a repository rule stating that edits intended to change reusable behavior must be made in `workflow/` or `templates/`, not in `dev/`.

2. **Maintainer skill**
   Add a dedicated maintainer skill that:
   - restates the authoritative-source rule
   - rebuilds `dev/` before validation
   - warns before editing inside `dev/`
   - routes exceptional `dev/` edits through `sdd dev diff` and `sdd dev promote`

3. **CLI protection**
   Add CLI checks that:
   - warn if a maintainer is about to promote from a dirty `dev/` workspace
   - identify files that cannot be promoted safely
   - refuse promotion of known generated-only files

4. **Optional pre-commit or validation hook**
   Detect suspicious commits that include `dev/` edits without corresponding authoritative-source changes.

### 11.3 Preferred implementation

The best near-term approach is:

- encode the rule in `AGENTS.md`
- implement the behavior in the CLI
- add a thin maintainer skill that calls the CLI correctly

This is better than relying on instructions alone because:

- rules reduce ambiguity
- CLI checks catch mistakes
- the skill makes the correct path convenient for the maintainer

### 11.4 Maintainer skill role

The maintainer-oriented skill should not contain business logic that the CLI lacks.

Its role should be:

- choose the right `sdd dev ...` command
- explain the development loop
- warn if the user asks for a change that would wrongly modify `dev/`
- help classify exploratory diffs

That keeps the safety model consistent with the rest of this plan:

- CLI is canonical
- skill is orchestration and guidance

---

## 12. Downstream update model for generated projects

This section defines how already-created user projects should continue receiving updates from this repository.

### 12.1 Non-goal

We should not treat generated projects as if they can safely receive upstream changes through:

- `git pull` from the template repository
- blind re-generation of the whole project
- skills that attempt to merge template changes without CLI support

Once a project is generated, it is its own repository and will often contain significant user-owned code. Upstream updates must therefore be explicit, scoped, and inspectable.

Additional decision:

- we do not need a legacy-adoption path for pre-refactor experimental projects in this repository ecosystem
- only projects generated after this refactor need to carry supported upgrade metadata

### 12.2 Update classes

Not every generated file should be upgraded the same way.

We should distinguish three classes:

1. **workflow updates**
   - `AGENTS.md`
   - `CLAUDE.md`
   - workflow playbook copies or wrappers
   - workflow helper scripts

2. **template infrastructure updates**
   - Docker and Compose files
   - CI workflows
   - lint, format, and test configuration
   - stack-level deployment and development scaffolding

3. **application code**
   - business logic
   - domain models after customization
   - frontend pages and features
   - backend feature code

Default rule:

- automatic upstream updates should target workflow-managed and template-managed assets
- application code should not be assumed safely auto-upgradeable

### 12.3 Provenance and ownership metadata

Every generated project should carry explicit metadata that makes upgrades transparent.

Recommended files:

- `.sdd-origin.yaml`
- `.sdd-lock.yaml`
- `.sdd/ownership.yaml`

Responsibilities:

- `.sdd-origin.yaml`
  Records metadata schema version, source repository, template id, workflow version, template version, and the source commit or tag used when the project was generated.

- `.sdd-lock.yaml`
  Records metadata schema version plus the exact installed workflow/template component versions currently applied to the generated project.

- `.sdd/ownership.yaml`
  Records metadata schema version and declares which paths are:
  - workflow-managed
  - template-managed
  - user-owned
  - merge-required

### 12.4 Metadata compatibility policy

Generated-project metadata must be versioned explicitly.

Rules:

- each `.sdd-*` metadata file must declare a schema version
- the CLI must support backward-compatible reads for a documented compatibility window
- if metadata is too old to upgrade safely, the CLI must stop and require an explicit metadata migration step
- metadata migrations must be reversible or regenerable from released source artifacts plus local project state

### 12.5 Baseline storage and materialization

The upgrade engine needs an exact prior baseline, not just version labels.

Decision:

- `.sdd-lock.yaml` should record the installed workflow/template release identifiers plus per-managed-path baseline hashes
- the CLI should reconstruct prior baselines from released artifacts when it needs full file content for merge operations
- hash mismatches between reconstructed baselines and recorded metadata must fail loudly because they indicate corruption or provenance drift

Why this model:

- version identifiers alone are not sufficient for trustworthy merge decisions
- per-path hashes make drift detection cheap and explicit
- released artifacts remain the source for reconstructing exact prior content

### 12.6 Ownership categories

The ownership model must be explicit because upgrade safety depends on it.

Suggested categories:

- `workflow-managed`
  Files that can be replaced or merged using workflow upgrade rules.

- `template-managed`
  Files that belong to the selected template's maintained infrastructure layer.

- `user-owned`
  Files that should be left untouched by automatic upstream updates unless the user explicitly opts in.

- `merge-required`
  Files where upstream improvements may be valuable but should always go through a reviewable merge flow.

### 12.7 Managed-file update algorithm

The upgrade engine must use a deterministic three-input model for managed files:

1. the last applied upstream baseline from the installed workflow/template release
2. the current local project file
3. the target upstream file from the requested release

Rules:

- if local matches baseline and target differs, replace safely
- if local differs from baseline and target matches baseline, keep local unchanged
- if both local and target differ from baseline, run a three-way merge
- if the merge is clean and the file is classified as auto-updateable, apply it
- if the merge is not clean, reclassify the file as `merge-required`
- `user-owned` files are never changed automatically

Deletion rules:

- if a managed file existed in the installed baseline and is removed in the target release, the CLI must treat this as a first-class change
- if the local file still matches the baseline, the file may be deleted automatically for `workflow-managed` or `template-managed` paths
- if the local file differs from the baseline, automatic deletion is not allowed and the file must become `merge-required`
- `user-owned` files are never deleted automatically
- deletion candidates must be shown explicitly in `sdd upgrade --check`

Operational requirements:

- `sdd upgrade --check` must show which algorithmic path each changed file took
- applied upgrades should be transactional at the command level where practical
- on failure, the CLI must either roll back applied file changes or leave a clearly recoverable staged state with a report
- merge output must be inspectable and must never silently discard local modifications

### 12.8 Upgrade lifecycle

The upgrade command should behave like a package manager plus a patch manager, not like a blind copier.

Recommended lifecycle:

1. read `.sdd-origin.yaml`, `.sdd-lock.yaml`, and `.sdd/ownership.yaml`
2. fetch or resolve the requested workflow/template target versions
3. compute the upstream delta
4. classify every affected file as:
   - safe auto-update
   - merge required
   - blocked because it is user-owned
5. show the full plan before applying
6. apply only safe updates automatically
7. generate a review report for merge-required or blocked files
8. update provenance/lock metadata only after the upgrade result is consistent

### 12.9 Default UX

The default user path should be review-first:

```bash
sdd upgrade --check
sdd upgrade workflow
sdd upgrade template
```

The command output should make ownership explicit. For example:

- `AGENTS.md`: auto-update
- `.github/workflows/ci.yml`: merge required
- `docker-compose.yml`: auto-update with local patch preserved
- `frontend/app/pages/index.vue`: skipped, user-owned

### 12.10 Preferred implementation model

The preferred implementation is a hybrid:

- the `sdd` CLI itself can be delivered as a versioned package or installable tool
- workflow and template file updates are applied as managed overlays
- ownership metadata determines what may be updated automatically

This is preferred over git-subtree, git-submodule, or full project regeneration because it is:

- more transparent to users
- easier to reason about file ownership
- better suited to mixed workflow/template/application repositories

### 12.11 Relationship to maintainer-side development

The downstream upgrade model and the maintainer `dev/` model are separate but aligned.

They share the same philosophy:

- one authoritative source
- explicit ownership
- explicit synchronization
- no hidden drift

But they use different commands:

- maintainers use `sdd dev ...` against `workflow/`, `templates/`, and generated `dev/` workspaces inside this repository
- downstream projects use `sdd upgrade ...` against provenance and ownership metadata recorded in their own repositories

---

## 13. How the current repository maps into the new model

---

### 13.1 Workflow-owned assets

These are the main assets that are now workflow-owned:

- `workflow/docs/playbooks/`
- the `sdd` CLI implementation
- the canonical derived-project `AGENTS` and `CLAUDE` source templates
- bootstrap logic that is stack-neutral
- integration orchestration logic

### 13.2 Template-owned assets

These now live under `templates/fastapi-nuxt/source/`:

- `app/`
- `frontend/`
- `alembic/`
- `nginx/`
- `Dockerfile.backend`
- `Dockerfile.frontend`
- `docker-compose*.yml`
- `alembic.ini`
- `entrypoint.sh`
- template-local stack docs
- stack-local bootstrap scripts
- stack-local gate helpers
- shipped runtime wrappers under `.claude/` and `plugins/sdd-workflow/`

### 13.3 Mixed assets that need redesign

- `README.md`
- any CI job that currently treats the reference stack as the repository identity

---

## 14. Implementation phases

### Phase 0. Freeze vocabulary and architecture

Status: completed

Objective:
lock in the `workflow + templates + CLI + skill` model before structural edits.

Tasks:

- adopt the term `workflow` in planning docs
- stop using `core` as the primary architectural label
- approve the removal of `human-instructions/`
- approve CLI-first integration

Exit criteria:

- maintainers can describe the architecture in under two minutes

### Phase 1. Inventory and remove dead conceptual weight

Status: completed enough for implementation

Objective:
separate active assets from legacy notes before moving files.

Tasks:

- classify all top-level files as workflow, template, runtime wrapper, dev fixture, maintainer docs, or dead weight
- confirm the two note files in `human-instructions/` are deleted
- create an ownership matrix for the current repo

Deliverable:

- `docs/WORKFLOW_TEMPLATE_OWNERSHIP_MATRIX.md`

Exit criteria:

- every major path has an explicit ownership label
- dead weight is called out explicitly

### Phase 2. Move canonical derived-project files out of `human-instructions/`

Status: completed

Objective:
eliminate the temporary directory and put shipped files where they belong.

Tasks:

- create `workflow/project-files/`
- move `AGENTS.for-new-projects.md` to `workflow/project-files/AGENTS.md.template`
- move `CLAUDE.for-new-projects.md` to `workflow/project-files/CLAUDE.md.template`
- update all references and generators
- remove `human-instructions/` after migration

Exit criteria:

- no bootstrap path depends on `human-instructions/`
- all canonical shipped files live under workflow-owned paths

### Phase 3. Introduce the workflow CLI skeleton

Status: completed for the initial command surface

Objective:
establish the canonical executable surface before deeper extraction.

Tasks:

- create the CLI entrypoint
- implement `sdd init` skeleton
- implement `sdd register-template` skeleton
- implement `sdd integrate` skeleton
- implement `sdd dev rebuild` skeleton
- implement `sdd dev diff` skeleton
- define `sdd dev promote` behavior and safety checks
- keep current behavior via thin compatibility wrappers where needed

Exit criteria:

- all future integration work has one canonical executable home

### Phase 4. Introduce generated template metadata

Status: completed for the current manifest schema and registration flow

Objective:
replace hidden assumptions with inspectable metadata without requiring large manual authoring effort.

Tasks:

- define a minimal `template.yaml`
- implement template inspection heuristics
- generate a draft manifest for the current FastAPI/Nuxt stack
- define how ambiguous detections are reported

Exit criteria:

- the current reference template can be represented by generated metadata plus small manual fixes

### Phase 5. Extract the reference stack into `templates/fastapi-nuxt/`

Status: completed for canonical source extraction

Objective:
make the current stack visibly a template rather than the repository identity.

Tasks:

- move stack files into `templates/fastapi-nuxt/`
- move stack-local docs with the template
- keep temporary compatibility shims only where necessary

Exit criteria:

- the reference stack is physically isolated as a template
- workflow development can still validate against it

### Phase 6. Rebuild initialization around `sdd init` + `sdd integrate`

Status: completed

Objective:
replace monolithic hardcoded bootstrap logic with workflow-driven integration.

Tasks:

- retire `scripts/init-project.sh` as the main source of truth
- move placeholder replacement into template-aware integration
- generate root `AGENTS.md` and `CLAUDE.md` from workflow templates
- make template selection explicit
- make `sdd integrate` capable of repairing missing managed workflow files for workflow-composed projects

Exit criteria:

- initialization no longer hardcodes one repo layout as architectural truth

Current state:

- `sdd init` now applies template bootstrap replacements directly (project naming placeholders, db-name placeholders, optional domain placeholders, `.env` generation) without requiring `scripts/init-project.sh`
- `sdd integrate --apply-template-init` can apply the same template bootstrap replacements to already integrated projects
- `--run-compat-init` remains available as a fallback legacy compatibility path, but is no longer the primary recommended flow
- template release-path validation no longer treats `scripts/init-project.sh` as a required canonical path; its presence is now compatibility-only

### Phase 7. Introduce downstream provenance and upgrade metadata

Status: completed

Objective:
make generated projects upgradeable without relying on blind regeneration or manual reverse-engineering.

Tasks:

- define `.sdd-origin.yaml`
- define `.sdd-lock.yaml`
- define `.sdd/ownership.yaml`
- define metadata schema version fields and compatibility rules
- define per-path baseline hash recording rules
- decide initial ownership defaults for workflow-managed, template-managed, user-owned, and merge-required paths
- ensure generated projects receive this metadata during initialization
- ensure `sdd integrate` can backfill this metadata into workflow-composed projects that are missing it

Exit criteria:

- every generated project has explicit provenance and ownership data
- downstream upgrades have enough metadata to build a reviewable plan

Current state:

- `sdd init` writes `.sdd-origin.yaml`, `.sdd-lock.yaml`, `.sdd/ownership.yaml`, and `.sdd/template-manifest.yaml` for every generated project
- metadata schema version checks are enforced during upgrade metadata loading for compatibility safety
- ownership defaults and baseline hash capture are generated centrally in CLI logic
- `sdd integrate` now repairs partially present `.sdd-*` metadata for workflow-composed projects by re-writing canonical metadata files

### Phase 8. Implement `sdd upgrade --check` and scoped upgrade flows

Status: completed

Objective:
give generated projects a transparent, explicit path for receiving upstream updates.

Tasks:

- implement `sdd upgrade --check`
- implement `sdd upgrade workflow`
- implement `sdd upgrade template`
- implement the first review-only planning path against current workspace canonical sources
- implement the first safe `--apply` path against current workspace canonical sources
- implement released-artifact resolution from version identifiers
- implement the managed-file three-way merge/update algorithm
- implement deletion handling for removed managed files
- add review reporting for merge-required and user-owned paths
- update lock metadata only after successful upgrades

Exit criteria:

- generated projects can preview and apply scoped workflow/template upgrades
- the upgrade output makes ownership decisions visible to the user

Current state:

- `sdd upgrade` now supports explicit released-artifact resolution from namespaced git tags
- `sdd upgrade --source workspace-current ...` remains available as a maintainer/debugging path
- safe `--apply` behavior is implemented for both workspace-current and released-artifact paths
- clean three-way text merges now promote eligible managed files from `merge-required` to auto-merge when the installed baseline can be reconstructed reliably
- maintainer-facing `sdd release status` and `sdd release validate` commands now make workflow/template release coordinates and tag expectations explicit before publishing component tags
- end-to-end CLI tests now exercise real `workflow/vX.Y.Z` and `template/<id>/vX.Y.Z` git tags through `git archive`-backed resolution, covering `sdd release status`, `sdd release validate --expect-existing-tags`, `sdd upgrade --check`, and `sdd upgrade --apply` against published artifacts
- `write_workflow_project_files` now accepts an explicit source directory so upgrade target and baseline snapshots render `AGENTS.md` / `CLAUDE.md` from the tagged `workflow/project-files/`, rather than accidentally falling back to the workspace copy when the workspace has drifted ahead of the installed or target release
- released-artifact E2E tests now verify scoped default-mode upgrades (`sdd upgrade workflow --apply` and `sdd upgrade template --apply`) advance only their respective lock component versions while leaving the non-target component pinned
- upgrade apply coverage now includes managed-file deletion handling that removes deleted workflow-managed paths from `.sdd-lock.yaml` baseline hashes
- upgrade metadata loading now reports all incompatible `.sdd-*` metadata schema versions together (instead of failing one file at a time), improving mixed-scope compatibility diagnostics
- workflow-scope partial apply outcomes now persist `.sdd-lock.yaml` pending markers even when no safe file operations were applied, and tests cover both zero-safe and mixed safe+blocked partial outcomes
- upgrade analysis now fails loudly when reconstructed installed baselines disagree with recorded `.sdd-lock.yaml` baseline hashes (hash mismatch or missing baseline path), and tests cover both integrity-failure cases
- compatibility-window policy is now enforced before baseline reconstruction: required components must resolve to installed release tags, except explicit `workspace-current` fallback when lock versions match the current checkout (or are non-release maintainer coordinates), and CLI tests now cover both allowed and blocked tag-unavailable cases with explicit diagnostics
- maintainer-facing upgrade/release docs now document the compatibility-window behavior explicitly, and release-E2E coverage now includes the released-artifact failure path when installed baseline tags are missing
- targeted phase-8 validation is green (`35` focused upgrade/release tests via `tests/test_sdd_cli.py -k "upgrade or release_status or release_validate"`)

### Phase 9. Rebuild gate dispatch around workflow-owned orchestration

Status: completed

Objective:
keep gate procedure reusable while allowing stack-specific execution.

Tasks:

- move stack-specific gate execution behind template metadata or adapter scripts
- keep the workflow playbook stack-neutral
- ensure `phase-gate` resolves commands from integrated template metadata

Exit criteria:

- gate behavior is reusable
- stack commands are template-owned

Current state:

- generated projects now receive `.sdd/template-manifest.yaml` during `sdd init` / `sdd integrate`
- `sdd gate resolve` now exposes the active gate helper/docs pair from installed template metadata
- the `phase-gate` playbook and shipped runtime wrappers now treat template metadata as the gate-dispatch source, while `docs/STACK.md` remains the human-readable command reference

### Phase 10. Rework docs and CI around the new architecture

Status: completed

Objective:
make the repository understandable and test the architecture we actually want.

Tasks:

- rewrite `README.md` around workflow + templates
- narrow `docs/STACK.md` into template-local responsibility
- split CI into workflow checks, template checks, and integration checks
- ensure failures make ownership clear
- add maintainer guidance for the authoritative-source rule
- add protection against accidental `dev/`-only commits where practical

Exit criteria:

- docs match the implementation model
- CI can distinguish workflow, template, and integration failures

Current state:

- `README.md` and maintainer docs now describe the `workflow/ + templates/ + sdd` architecture directly
- CI is now split into ownership-oriented jobs:
  - `Workflow Contract`
  - `Template Contract`
  - `Integration CLI`
  - `Release E2E`
  - template runtime jobs for backend, frontend, and image build
- E2E remains part of the local phase-gate path, but is no longer a default CI requirement for shipped templates
- `sdd release validate` now supports `--scope workflow|template|all` and `--skip-tag-checks`, so everyday CI can validate component structure without pretending each run is a release event
- release-path tests are marked `@pytest.mark.release_e2e` and run in an isolated `Release E2E` CI job so regressions in the released-artifact resolution path are visible as such; the `Integration CLI` job excludes this marker to avoid double-running the ephemeral-tag fixtures

### Phase 11. Add template-authoring automation and guidance

Status: completed

Objective:
make adding templates realistic for maintainers.

Tasks:

- document how to create a template
- document how to run `sdd register-template`
- document how to review and fix generated metadata
- add examples of adapter scripts only for cases where manifest fields are insufficient

Exit criteria:

- a maintainer can add a second template without reverse-engineering the first one

Current state:

- `sdd register-template` now produces a richer `draft_manifest` with inferred package managers, technologies, init hooks, gate metadata, and smoke metadata
- `sdd register-template --write` can bootstrap `template.yaml` for a new template directory, while still requiring human review for ambiguous fields
- maintainer guidance for this loop now lives in `docs/TEMPLATE_AUTHORING.md`
- maintainer release procedure — pre-release validation, namespaced tag publishing, and post-release checks against `workflow/vX.Y.Z` and `template/<id>/vX.Y.Z` — is documented in `docs/RELEASE.md` and referenced from `AGENTS.md`

### Phase 12. Add maintainer AI safety tooling

Status: completed

Objective:
make the correct maintainer flow easy even when development happens through an AI agent.

Tasks:

- add a repository rule to `AGENTS.md`
- add a maintainer-oriented skill for template-repo development
- make `sdd dev promote` reject unsafe reverse-sync targets
- make CLI output clearly distinguish authoritative files from generated files

Exit criteria:

- an AI agent working in this repository is guided toward authoritative files by default
- accidental long-lived `dev/` edits are easier to detect and harder to promote blindly

Current state:

- `AGENTS.md` now states explicitly that `dev/` is a disposable validation lab and not a canonical edit target
- `sdd dev diff` now distinguishes authoritative reverse-sync candidates from generated-only files
- `sdd dev promote` now blocks generated-only paths such as rendered project files and dev metadata, while mapping reviewable changes back to their authoritative workflow/template targets
- a repo-only maintainer skill now lives at `.codex/skills/template-repo-maintainer/SKILL.md` to steer AI-assisted template work toward authoritative sources and the `sdd` validation loop

### Phase 13. Second-template proving step

Status: completed

Objective:
prove the architecture is not accidentally shaped around FastAPI/Nuxt.

Tasks:

- add a materially different second template
- run `sdd init`, `sdd integrate`, `sdd gate resolve`, `sdd register-template`, and `sdd upgrade --check` against it
- extend CI/template-contract validation so the second template is not invisible

Exit criteria:

- the workflow can integrate at least one non-identical template

Current status:

- `templates/fastapi-react-router/` now exists as the second canonical template
- it replaces the Nuxt frontend with React 19 + React Router SSR while keeping the reusable workflow/backend boundary intact
- `sdd register-template` correctly infers React Router-specific technologies for the new template
- CLI tests now exercise init/gate/upgrade/registration flows against both `fastapi-nuxt` and `fastapi-react-router`
- CI template-contract validation now runs for both templates
- repo CI now validates backend lint/tests, frontend checks, and image builds for both templates, while keeping Playwright E2E local-only by default

---

## 14.1 Active execution queue (as of 2026-04-24)

No unresolved implementation phases remain.

Immediate next step:

- keep this refactor plan closed and track any future upgrade hardening as new scoped backlog items (instead of reopening phase execution here)

Post-plan hardening log:

- 2026-04-24: completed first scoped follow-up by hardening release-archive extraction in `extract_git_tree` (`tarfile.extractall(..., filter="data")`) and adding regression coverage in `tests/test_sdd_cli.py`
- 2026-04-24: hardened `sdd release validate` scope behavior with regression tests proving template-scope validation can continue without a resolvable workflow package version (warning path), while `all`/`workflow` scopes still fail fast when workflow version resolution is required

---

## 15. Risks and mitigation

### Risk 1. The CLI becomes a pile of hidden assumptions

Mitigation:

- keep generated metadata explicit and inspectable
- prefer manifest data over hardcoded branching
- validate the manifest in CI

### Risk 2. The skill starts duplicating CLI behavior

Mitigation:

- treat CLI as canonical
- keep skills thin and wrapper-like

### Risk 3. Template inspection is too magical and unreliable

Mitigation:

- keep the manifest small
- mark low-confidence detections explicitly
- require review only for ambiguous fields

### Risk 4. We move files before the execution path is ready

Mitigation:

- create the CLI skeleton first
- add temporary compatibility shims during migration

### Risk 5. Old generic notes keep polluting canonical workflow paths

Mitigation:

- remove `human-instructions/`
- keep only maintained, canonical files under workflow-owned directories
- delete obsolete side notes instead of carrying them into the new architecture

### Risk 6. `dev/` becomes a shadow source of truth

Mitigation:

- make the authoritative-source rule explicit
- keep `dev/` reproducible and disposable
- provide `sdd dev diff` and `sdd dev promote` for exceptional debugging cases only
- add AI-agent guardrails in repository rules, skills, and CLI checks

### Risk 7. Generated projects cannot be upgraded safely after local customization

Mitigation:

- record provenance and ownership metadata in every generated project
- default upgrades to `--check` review mode
- treat application code as user-owned unless explicitly classified otherwise
- keep upgrade output explicit about which files were updated, skipped, or blocked

### Risk 8. Release sourcing becomes ambiguous or branch-driven

Mitigation:

- resolve upgrades from tagged releases by default
- store immutable version identifiers in generated-project metadata
- reject ambiguous branch-like version targets unless the user explicitly opts into a maintainer/debugging mode

### Risk 9. Metadata evolution breaks older generated projects

Mitigation:

- version every manifest and generated-project metadata file explicitly
- maintain a documented backward-compatibility window
- fail with an explicit migration path instead of silently interpreting unknown schema versions

### Risk 10. Hook execution becomes an implicit code-execution trap

Mitigation:

- require all hooks and adapters to be declared explicitly in template metadata
- treat external-template hook execution as opt-in
- surface hook execution in dry-run/reporting output

### Risk 11. Deletions during upgrade remove user-important files

Mitigation:

- treat upstream deletions as explicit upgrade events
- only auto-delete when the local file still matches baseline
- escalate locally modified deletions to `merge-required`

---

## 16. Validation rules

Each phase is accepted only if:

1. the ownership boundary is clearer than before
2. the reference template still runs through the workflow
3. docs point to the real source of truth
4. the CLI path is becoming more central, not less

Lightweight acceptance questions:

- Can a maintainer explain the workflow/template split quickly?
- Can the current FastAPI/Nuxt stack still be initialized and validated?
- Can a future template be added without editing many unrelated files?
- Is the skill still a wrapper, not the implementation?
- Is `dev/` still clearly non-authoritative?
- Would an AI agent be steered toward editing authoritative sources by default?
- Can a generated project explain where it came from and what parts are safe to upgrade?
- Does `sdd upgrade --check` produce a clear review plan before file changes happen?
- Is every supported upgrade target backed by a released, inspectable artifact?
- Are manifest and `.sdd-*` schema versions explicit and validated?
- Are hook executions explicit and visible before they run?
- Are managed-file deletions shown and classified safely?

---

## 17. Early decisions settled by this plan

These decisions are now the default implementation direction:

1. Use `workflow/` and `templates/` as the main architectural pairing.
2. Use a CLI as the canonical integration mechanism.
3. Keep skills as thin wrappers over the CLI.
4. Replace manual contract authoring with generated integration metadata.
5. Remove `human-instructions/`.
6. Move canonical derived-project instruction templates into `workflow/project-files/`.
7. Delete `how_to_create_skills.md` and `vs_code_settings_up.md` as non-pipeline material.
8. Treat `dev/` as a generated integration lab, not an authoritative source tree.
9. Add maintainer `sdd dev ...` commands for rebuild, diff, run, promote, and clean flows.
10. Add explicit AI-agent guardrails so template-repo improvements default to `workflow/` and `templates/`.
11. Give every generated project provenance, lock, and ownership metadata.
12. Deliver downstream updates through `sdd upgrade ...`, with `--check` as the default review path.
13. Treat application code in generated projects as user-owned by default during upstream upgrades.
14. Publish workflow/template upgrade targets from tagged releases, not floating branches.
15. Use explicit schema versioning for `template.yaml` and `.sdd-*` metadata.
16. Use a deterministic three-way merge/update model for managed-file upgrades.
17. Make `workflow/docs/playbooks/` the canonical home for workflow playbooks.
18. Use namespaced component tags for workflow and template releases.
19. Record per-path baseline hashes in `.sdd-lock.yaml` and reconstruct prior content from released artifacts when needed.
20. Make `sdd integrate` idempotent and repair-oriented for partial prior state.
21. Treat template hook execution as explicit, declared, and trust-scoped.
22. Treat managed-file deletions as explicit upgrade events with baseline-aware safety rules.

---

## 18. First implementation milestone

The first practical milestone was:

> The terminology is fixed, `human-instructions/` is gone, the workflow-owned project templates have moved, a minimal `sdd` CLI exists as the canonical integration surface, the reference stack has been extracted under `templates/fastapi-nuxt/`, and the repository root is no longer a compatibility product snapshot.

That milestone is now complete. It was valuable because it:

- removes semantic confusion early
- gives the refactor a real executable center
- reduces future migration risk
- starts paying down temporary structure immediately

---

## 19. Final summary

The repository should evolve from:

- one mixed package that bundles workflow logic, template assets, runtime wrappers, and generic notes

to:

- one reusable **workflow**
- one or more selectable **templates**
- one canonical **CLI** for inspection, initialization, and integration
- one thin **skill** layer for AI-assisted orchestration
- one generated **dev/** lab for maintainer validation
- one explicit **upgrade** path for generated downstream projects
- one clear separation between canonical workflow assets and optional maintainer notes

The central implementation idea is:

- developers create templates
- tooling analyzes them
- tooling generates the integration metadata it needs
- the workflow CLI performs deterministic integration
- maintainers validate changes in `dev/` but promote them back into authoritative sources
- generated projects receive explicit provenance and ownership metadata so upstream updates remain reviewable

This keeps the user experience simple without hiding the system behind undocumented behavior.
