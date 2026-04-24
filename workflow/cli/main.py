from __future__ import annotations

import filecmp
import fnmatch
import hashlib
import io
import json
import os
import re
import secrets
import shutil
import subprocess
import tarfile
import tempfile
import tomllib
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Any, Literal

import typer
import yaml

TEMPLATE_ALIASES = {
    "reference-stack": "fastapi-nuxt",
    "current-repo": "fastapi-nuxt",
}

IGNORE_NAMES = {
    ".git",
    ".venv",
    ".pytest_cache",
    ".mypy_cache",
    "__pycache__",
    "node_modules",
    ".nuxt",
    ".output",
    "playwright-report",
    "test-results",
    ".sdd-dev-state.json",
    "dist",
    "build",
    "dev",
    "settings.local.json",
}

METADATA_SCHEMA_VERSION = "0.1"

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Canonical SDD workflow CLI for initialization, integration, and maintainer dev tasks.",
)
dev_app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Maintainer commands for generated dev workspaces.",
)
gate_app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Inspect gate-dispatch metadata for generated projects.",
)
release_app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Maintainer commands for inspecting and validating workflow/template component releases.",
)
app.add_typer(dev_app, name="dev")
app.add_typer(gate_app, name="gate")
app.add_typer(release_app, name="release")


@dataclass
class DiffSummary:
    changed: list[str]
    only_in_repo: list[str]
    only_in_dev: list[str]


@dataclass
class TemplateManifest:
    template_id: str
    display_name: str
    version: str
    manifest_schema_version: str
    source_dir: Path
    manifest_path: Path
    technologies: list[str]
    init_hooks: list[dict[str, Any]]


@dataclass
class OwnershipRules:
    workflow_managed: list[str]
    template_managed: list[str]
    user_owned: list[str]
    merge_required: list[str]


@dataclass
class UpgradeEntry:
    path: str
    ownership: str
    action: str
    reason: str
    local_exists: bool
    target_exists: bool
    baseline_present: bool


@dataclass
class UpgradeAnalysis:
    entries: list[UpgradeEntry]
    target_hashes: dict[str, str]
    target_versions: dict[str, str]
    merged_contents: dict[str, str]


@dataclass
class ResolvedUpgradeTarget:
    resolution: str
    workflow_version: str
    template_version: str
    manifest: TemplateManifest
    workflow_source: str
    template_source: str
    workflow_tag: str | None = None
    template_tag: str | None = None


def repo_root() -> Path:
    cwd = Path.cwd().resolve()
    for candidate in (cwd, *cwd.parents):
        if (candidate / "workflow").is_dir() and (candidate / "templates").is_dir():
            return candidate
    return installation_root()


def installation_root() -> Path:
    return Path(__file__).resolve().parents[2]


def templates_dir() -> Path:
    return repo_root() / "templates"


def canonical_playbook_dir() -> Path:
    return repo_root() / "workflow" / "docs" / "playbooks"


def derived_project_templates_dir() -> Path:
    return repo_root() / "workflow" / "project-files"


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise typer.BadParameter(f"Template manifest must be a mapping: {path}")
    return data


def load_yaml_file_if_exists(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return load_yaml(path)


def utc_timestamp() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def slug_to_display_name(slug: str) -> str:
    words = [part for part in slug.replace("_", "-").split("-") if part]
    return " ".join(word[:1].upper() + word[1:] for word in words) or slug


def slugify_project_name(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9-]+", "-", value.strip().lower())
    normalized = re.sub(r"-{2,}", "-", normalized).strip("-")
    if not normalized:
        raise typer.BadParameter("Project name cannot be empty after slug normalization.")
    return normalized


def strip_template_header(text: str) -> str:
    lines = text.splitlines()
    if "---" not in lines:
        return text
    separator_index = lines.index("---")
    stripped = lines[separator_index + 1 :]
    if stripped and stripped[0] == "":
        stripped = stripped[1:]
    return "\n".join(stripped).rstrip() + "\n"


def render_project_instruction(template_path: Path, project_display_name: str) -> str:
    content = template_path.read_text(encoding="utf-8")
    return strip_template_header(content).replace("[PROJECT_NAME]", project_display_name)


def write_workflow_project_files(
    destination: Path,
    project_slug: str,
    project_files_source: Path | None = None,
) -> list[str]:
    project_display_name = slug_to_display_name(project_slug)
    source_root = project_files_source or derived_project_templates_dir()
    generated_paths: list[str] = []
    project_files = {
        "AGENTS.md": source_root / "AGENTS.md.template",
        "CLAUDE.md": source_root / "CLAUDE.md.template",
    }
    for filename, template_path in project_files.items():
        rendered = render_project_instruction(template_path, project_display_name)
        output_path = destination / filename
        output_path.write_text(rendered, encoding="utf-8")
        generated_paths.append(filename)
    return generated_paths


def git_output(*args: str) -> str | None:
    result = subprocess.run(
        ["git", *args],
        cwd=repo_root(),
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def git_lines(*args: str) -> list[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=repo_root(),
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def detect_repo_provenance() -> dict[str, Any]:
    remote_url = git_output("config", "--get", "remote.origin.url")
    head_commit = git_output("rev-parse", "HEAD")
    short_ref = git_output("describe", "--always", "--dirty", "--tags")
    return {
        "repository": remote_url or str(repo_root()),
        "revision": head_commit or "workspace",
        "describe": short_ref or "workspace",
    }


def repo_is_dirty() -> bool:
    return bool(git_lines("status", "--short"))


def load_repo_package_version() -> str:
    pyproject_path = repo_root() / "pyproject.toml"
    try:
        payload = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, tomllib.TOMLDecodeError) as exc:
        raise typer.BadParameter(f"Could not read repository package version from {pyproject_path}: {exc}") from exc

    project = payload.get("project")
    if not isinstance(project, dict):
        raise typer.BadParameter(f"`[project]` is missing from {pyproject_path}.")
    version = project.get("version")
    if not isinstance(version, str) or not version.strip():
        raise typer.BadParameter(f"`project.version` is missing from {pyproject_path}.")
    return version.strip()


def default_ownership_rules() -> OwnershipRules:
    return OwnershipRules(
        workflow_managed=[
            "AGENTS.md",
            "CLAUDE.md",
            "workflow/**",
        ],
        template_managed=[
            ".agents/plugins/marketplace.json",
            ".claude/**",
            ".dockerignore",
            ".env.example",
            ".gitattributes",
            ".github/workflows/**",
            ".gitignore",
            ".nvmrc",
            ".pre-commit-config.yaml",
            ".python-version",
            ".vscode/settings.json",
            "DEPLOY.md",
            "Dockerfile.backend",
            "Dockerfile.frontend",
            "Makefile",
            "alembic.ini",
            "docker-compose.ci.yml",
            "docker-compose.override.yml",
            "docker-compose.prod.yml",
            "docker-compose.yml",
            "docs/STACK.md",
            "entrypoint.sh",
            "nginx/**",
            "plugins/sdd-workflow/**",
            "scripts/**",
        ],
        user_owned=[
            "README.md",
            "TODO.md",
            "alembic/**",
            "app/**",
            "docs/AGENT_SETUP.md",
            "docs/CHANGELOG.md",
            "docs/CONTEXT.md",
            "docs/DECISIONS.md",
            "docs/E2E_PIPELINE_CHECKLIST.md",
            "docs/KNOWN_GOTCHAS.md",
            "docs/PHASE_01.md",
            "docs/PHASE_TEMPLATE.md",
            "docs/SPEC.md",
            "docs/STATE.md",
            "frontend/**",
            "tests/**",
        ],
        merge_required=[
            "pyproject.toml",
            "uv.lock",
        ],
    )


def classify_path(path: str, rules: OwnershipRules) -> str:
    for category, patterns in (
        ("workflow-managed", rules.workflow_managed),
        ("template-managed", rules.template_managed),
        ("merge-required", rules.merge_required),
        ("user-owned", rules.user_owned),
    ):
        if any(path_matches_pattern(path, pattern) for pattern in patterns):
            return category
    return "user-owned"


def path_matches_pattern(path: str, pattern: str) -> bool:
    if pattern.endswith("/**"):
        prefix = pattern[:-3]
        return path == prefix or path.startswith(prefix + "/")
    return fnmatch.fnmatch(path, pattern)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def metadata_dir(project_root: Path) -> Path:
    return project_root / ".sdd"


def project_template_manifest_path(project_root: Path) -> Path:
    return metadata_dir(project_root) / "template-manifest.yaml"


def load_template_manifest(template_ref: str) -> TemplateManifest:
    normalized_ref = TEMPLATE_ALIASES.get(template_ref, template_ref)
    template_dir = (templates_dir() / normalized_ref).resolve()
    manifest_path = template_dir / "template.yaml"
    if not manifest_path.exists():
        available = sorted(path.name for path in templates_dir().iterdir() if path.is_dir())
        supported = ", ".join(available) or "<none>"
        raise typer.BadParameter(f"Unknown template '{template_ref}'. Available templates: {supported}.")

    payload = load_yaml(manifest_path)
    source_dir_name = str(payload.get("source_dir", "source"))
    source_dir = (template_dir / source_dir_name).resolve()
    if not source_dir.is_dir():
        raise typer.BadParameter(f"Template source directory does not exist for '{template_ref}': {source_dir}")

    return TemplateManifest(
        template_id=str(payload.get("template_id", template_dir.name)),
        display_name=str(payload.get("display_name", template_dir.name)),
        version=str(payload.get("version", "0.1.0")),
        manifest_schema_version=str(payload.get("manifest_schema_version", "0.1")),
        source_dir=source_dir,
        manifest_path=manifest_path,
        technologies=list(payload.get("technologies", [])),
        init_hooks=list(payload.get("init_hooks", [])),
    )


def ensure_empty_target(target_dir: Path) -> None:
    if target_dir.exists():
        if not target_dir.is_dir():
            raise typer.BadParameter(f"Target path exists and is not a directory: {target_dir}")
        if any(target_dir.iterdir()):
            raise typer.BadParameter(
                f"Target directory is not empty: {target_dir}. "
                "Use a new directory or clean it before running `sdd init`."
            )


def copy_directory_contents(source: Path, destination: Path) -> None:
    if destination.exists():
        destination.mkdir(parents=True, exist_ok=True)
    else:
        destination.mkdir(parents=True)

    ignore = shutil.ignore_patterns(*sorted(IGNORE_NAMES))
    for item in source.iterdir():
        if item.name in IGNORE_NAMES:
            continue
        target = destination / item.name
        if item.is_dir():
            shutil.copytree(item, target, ignore=ignore)
        else:
            shutil.copy2(item, target)


def materialize_project(destination: Path, manifest: TemplateManifest) -> None:
    copy_directory_contents(manifest.source_dir, destination)
    workflow_target = destination / "workflow"
    if workflow_target.exists():
        shutil.rmtree(workflow_target)
    shutil.copytree(repo_root() / "workflow", workflow_target)


def collect_non_user_owned_hashes(project_root: Path, rules: OwnershipRules) -> tuple[dict[str, str], dict[str, str]]:
    workflow_hashes: dict[str, str] = {}
    template_hashes: dict[str, str] = {}
    for rel_path, abs_path in collect_files(project_root).items():
        category = classify_path(rel_path, rules)
        if category == "user-owned":
            continue
        if category == "workflow-managed":
            workflow_hashes[rel_path] = sha256_file(abs_path)
        else:
            template_hashes[rel_path] = sha256_file(abs_path)
    return workflow_hashes, template_hashes


def build_origin_payload(
    destination: Path,
    manifest: TemplateManifest,
    project_slug: str,
) -> dict[str, Any]:
    provenance = detect_repo_provenance()
    return {
        "project_metadata_version": METADATA_SCHEMA_VERSION,
        "generated_at": utc_timestamp(),
        "project": {
            "slug": project_slug,
            "display_name": slug_to_display_name(project_slug),
            "path": str(destination.resolve()),
        },
        "source": provenance,
        "workflow": {
            "version": provenance["describe"],
            "source_subdir": "workflow",
        },
        "template": {
            "id": manifest.template_id,
            "display_name": manifest.display_name,
            "version": manifest.version,
            "manifest_schema_version": manifest.manifest_schema_version,
            "source_subdir": str(manifest.manifest_path.parent.relative_to(repo_root())),
        },
    }


def build_lock_payload(
    workflow_hashes: dict[str, str],
    template_hashes: dict[str, str],
    manifest: TemplateManifest,
) -> dict[str, Any]:
    provenance = detect_repo_provenance()
    return {
        "project_metadata_version": METADATA_SCHEMA_VERSION,
        "generated_at": utc_timestamp(),
        "workflow": {
            "version": provenance["describe"],
            "baseline_hashes": workflow_hashes,
        },
        "template": {
            "id": manifest.template_id,
            "version": manifest.version,
            "manifest_schema_version": manifest.manifest_schema_version,
            "baseline_hashes": template_hashes,
        },
    }


def build_ownership_payload(rules: OwnershipRules) -> dict[str, Any]:
    return {
        "project_metadata_version": METADATA_SCHEMA_VERSION,
        "generated_at": utc_timestamp(),
        "ownership": {
            "workflow-managed": rules.workflow_managed,
            "template-managed": rules.template_managed,
            "user-owned": rules.user_owned,
            "merge-required": rules.merge_required,
        },
    }


def write_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(payload, handle, sort_keys=False, allow_unicode=True)


def project_manifest_payload(manifest: TemplateManifest) -> dict[str, Any]:
    payload = load_yaml(manifest.manifest_path).copy()
    payload.setdefault("manifest_schema_version", manifest.manifest_schema_version)
    payload.setdefault("template_id", manifest.template_id)
    payload.setdefault("display_name", manifest.display_name)
    payload.setdefault("version", manifest.version)
    payload.setdefault("source_dir", ".")
    return payload


def write_project_template_manifest(project_root: Path, manifest: TemplateManifest) -> str:
    relative_manifest_path = Path(".sdd") / "template-manifest.yaml"
    payload = project_manifest_payload(manifest)
    payload["source_dir"] = "."
    write_yaml(project_root / relative_manifest_path, payload)
    return str(relative_manifest_path)


def load_project_ownership_rules(project_root: Path) -> OwnershipRules:
    ownership_path = metadata_dir(project_root) / "ownership.yaml"
    payload = load_yaml(ownership_path)
    ownership = payload.get("ownership")
    if not isinstance(ownership, dict):
        raise typer.BadParameter(f"Ownership metadata is missing the 'ownership' mapping: {ownership_path}")
    return OwnershipRules(
        workflow_managed=list(ownership.get("workflow-managed", [])),
        template_managed=list(ownership.get("template-managed", [])),
        user_owned=list(ownership.get("user-owned", [])),
        merge_required=list(ownership.get("merge-required", [])),
    )


def incompatible_project_metadata_versions(
    payloads: list[tuple[Path, dict[str, Any]]],
) -> list[tuple[Path, Any]]:
    incompatible: list[tuple[Path, Any]] = []
    for path, payload in payloads:
        version = payload.get("project_metadata_version")
        if version != METADATA_SCHEMA_VERSION:
            incompatible.append((path, version))
    return incompatible


def write_project_metadata(
    destination: Path,
    manifest: TemplateManifest,
    project_slug: str,
) -> list[str]:
    rules = default_ownership_rules()
    workflow_hashes, template_hashes = collect_non_user_owned_hashes(destination, rules)
    origin_path = destination / ".sdd-origin.yaml"
    lock_path = destination / ".sdd-lock.yaml"
    ownership_path = metadata_dir(destination) / "ownership.yaml"
    project_template_manifest = write_project_template_manifest(destination, manifest)
    write_yaml(origin_path, build_origin_payload(destination, manifest, project_slug))
    write_yaml(lock_path, build_lock_payload(workflow_hashes, template_hashes, manifest))
    write_yaml(ownership_path, build_ownership_payload(rules))
    return [
        ".sdd-origin.yaml",
        ".sdd-lock.yaml",
        ".sdd/ownership.yaml",
        project_template_manifest,
    ]


def load_upgrade_metadata(
    project_root: Path,
) -> tuple[dict[str, Any], dict[str, Any], OwnershipRules]:
    origin_path = project_root / ".sdd-origin.yaml"
    lock_path = project_root / ".sdd-lock.yaml"
    ownership_path = metadata_dir(project_root) / "ownership.yaml"
    missing = [path for path in (origin_path, lock_path, ownership_path) if not path.exists()]
    if missing:
        joined = ", ".join(str(path.relative_to(project_root)) for path in missing)
        raise typer.BadParameter(
            f"Upgrade metadata is incomplete. Missing: {joined}. Run `sdd integrate --check` or `sdd integrate` first."
        )

    origin_payload = load_yaml(origin_path)
    lock_payload = load_yaml(lock_path)
    ownership_payload = load_yaml(ownership_path)
    incompatible_metadata = incompatible_project_metadata_versions(
        [
            (origin_path, origin_payload),
            (lock_path, lock_payload),
            (ownership_path, ownership_payload),
        ]
    )
    if incompatible_metadata:
        details = "; ".join(f"{path.relative_to(project_root)}={version!r}" for path, version in incompatible_metadata)
        raise typer.BadParameter(
            "Unsupported project metadata version in upgrade metadata files. "
            f"Expected {METADATA_SCHEMA_VERSION!r}. Found: {details}."
        )
    rules = load_project_ownership_rules(project_root)
    return origin_payload, lock_payload, rules


def load_project_template_manifest(project_root: Path) -> dict[str, Any]:
    manifest_path = project_template_manifest_path(project_root)
    if not manifest_path.exists():
        raise typer.BadParameter(
            "Generated project is missing `.sdd/template-manifest.yaml`. "
            "Run `sdd integrate` to repair template metadata."
        )
    payload = load_yaml(manifest_path)
    manifest_schema = payload.get("manifest_schema_version")
    if not isinstance(manifest_schema, str) or not manifest_schema:
        raise typer.BadParameter(f"Installed template manifest is missing `manifest_schema_version`: {manifest_path}")
    return payload


def normalize_release_version(version: str) -> str:
    stripped = version.strip()
    if not stripped:
        raise typer.BadParameter("Release version cannot be empty.")
    return stripped if stripped.startswith("v") else f"v{stripped}"


def parse_release_semver(version: str) -> tuple[int, int, int]:
    match = re.fullmatch(r"v(\d+)\.(\d+)\.(\d+)", version)
    if not match:
        raise typer.BadParameter(
            f"Unsupported release version format: {version!r}. Expected semantic versions like v1.2.3."
        )
    return tuple(int(part) for part in match.groups())


def latest_release_tag(tags: list[str], prefix: str) -> str:
    if not tags:
        raise typer.BadParameter(f"No released artifacts found for {prefix.rstrip('/')} in this repository.")
    try:
        return max(tags, key=lambda tag: parse_release_semver(tag.removeprefix(prefix)))
    except typer.BadParameter as exc:
        raise typer.BadParameter(f"Could not determine the latest release tag under {prefix!r}: {exc}") from exc


def resolve_requested_versions(requested_targets: list[str]) -> dict[str, Any]:
    resolved: dict[str, Any] = {}
    for raw in requested_targets:
        if raw.startswith("workflow@"):
            if "workflow" in resolved:
                raise typer.BadParameter("Pass at most one `--to workflow@<version>` value.")
            resolved["workflow"] = normalize_release_version(raw.split("@", 1)[1])
            continue
        if raw.startswith("template@"):
            parts = raw.split("@")
            if len(parts) != 3 or not parts[1] or not parts[2]:
                raise typer.BadParameter("Template targets must use `template@<template-id>@<version>`.")
            if "template" in resolved:
                raise typer.BadParameter("Pass at most one template `--to` target.")
            resolved["template"] = {
                "id": parts[1],
                "version": normalize_release_version(parts[2]),
            }
            continue
        raise typer.BadParameter(
            f"Unsupported `--to` value {raw!r}. Use `workflow@<version>` or `template@<template-id>@<version>`."
        )
    return resolved


def release_tags_for_prefix(prefix: str) -> list[str]:
    return git_lines("tag", "--list", f"{prefix}*")


def resolve_release_tag(prefix: str, requested_version: str | None) -> str:
    if requested_version is not None:
        tag = f"{prefix}{normalize_release_version(requested_version)}"
        if tag not in release_tags_for_prefix(prefix):
            raise typer.BadParameter(f"Requested release tag does not exist: {tag}")
        return tag
    return latest_release_tag(release_tags_for_prefix(prefix), prefix)


def load_release_template_manifest(template_id: str, template_tag: str) -> TemplateManifest:
    manifest_relpath = f"templates/{template_id}/template.yaml"
    result = subprocess.run(
        ["git", "show", f"{template_tag}:{manifest_relpath}"],
        cwd=repo_root(),
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise typer.BadParameter(f"Template manifest {manifest_relpath} is missing from release tag {template_tag}.")
    payload = yaml.safe_load(result.stdout) or {}
    if not isinstance(payload, dict):
        raise typer.BadParameter(f"Template manifest at {manifest_relpath} in {template_tag} is not a mapping.")
    source_dir_name = str(payload.get("source_dir", "source"))
    return TemplateManifest(
        template_id=str(payload.get("template_id", template_id)),
        display_name=str(payload.get("display_name", template_id)),
        version=str(payload.get("version", normalize_release_version(template_tag.split("/")[-1]))),
        manifest_schema_version=str(payload.get("manifest_schema_version", "0.1")),
        source_dir=Path(f"templates/{template_id}/{source_dir_name}"),
        manifest_path=Path(manifest_relpath),
        technologies=list(payload.get("technologies", [])),
        init_hooks=list(payload.get("init_hooks", [])),
    )


def extract_git_tree(tag: str, repo_path: str, destination: Path) -> None:
    result = subprocess.run(
        ["git", "archive", "--format=tar", tag, repo_path],
        cwd=repo_root(),
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise typer.BadParameter(f"Could not extract {repo_path} from {tag}.")
    destination.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(result.stdout)) as archive:
        archive.extractall(destination, filter="data")


def latest_release_version(prefix: str) -> str | None:
    tags = release_tags_for_prefix(prefix)
    if not tags:
        return None
    return latest_release_tag(tags, prefix).removeprefix(prefix)


def parse_docs_anchor_target(raw: str) -> str:
    return raw.split("#", 1)[0]


def gate_dispatch_payload_from_manifest(
    project_root: Path,
    manifest_payload: dict[str, Any],
) -> dict[str, Any]:
    gate_payload = manifest_payload.get("gate")
    if not isinstance(gate_payload, dict):
        raise typer.BadParameter(
            "Installed template manifest is missing the `gate` mapping required for gate dispatch."
        )
    helper_script = gate_payload.get("helper_script")
    stack_docs = gate_payload.get("stack_docs")
    smoke_payload = manifest_payload.get("smoke")
    smoke_docs_anchor = smoke_payload.get("docs_anchor") if isinstance(smoke_payload, dict) else None

    if not isinstance(helper_script, str) or not helper_script:
        raise typer.BadParameter("Installed template manifest is missing `gate.helper_script`.")
    if not isinstance(stack_docs, str) or not stack_docs:
        raise typer.BadParameter("Installed template manifest is missing `gate.stack_docs`.")

    helper_path = project_root / helper_script
    stack_docs_path = project_root / stack_docs
    smoke_docs_path = (
        project_root / parse_docs_anchor_target(smoke_docs_anchor)
        if isinstance(smoke_docs_anchor, str) and smoke_docs_anchor
        else None
    )

    return {
        "template": {
            "id": manifest_payload.get("template_id"),
            "display_name": manifest_payload.get("display_name"),
            "version": manifest_payload.get("version"),
            "manifest_schema_version": manifest_payload.get("manifest_schema_version"),
        },
        "gate": {
            "helper_script": helper_script,
            "helper_script_path": str(helper_path.resolve()),
            "helper_script_exists": helper_path.exists(),
            "stack_docs": stack_docs,
            "stack_docs_path": str(stack_docs_path.resolve()),
            "stack_docs_exists": stack_docs_path.exists(),
            "smoke_docs_anchor": smoke_docs_anchor,
            "smoke_docs_path": str(smoke_docs_path.resolve()) if smoke_docs_path else None,
            "smoke_docs_exists": smoke_docs_path.exists() if smoke_docs_path else None,
        },
        "message": (
            "Gate dispatch is resolved from `.sdd/template-manifest.yaml`; "
            "`docs/STACK.md` remains the human-readable stack reference."
        ),
    }


def validate_template_manifest_paths(manifest: TemplateManifest) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    source_root = manifest.source_dir
    if not source_root.is_dir():
        errors.append(f"Template source directory is missing: {source_root}")
        return errors, warnings

    manifest_payload = load_yaml(manifest.manifest_path)
    for required_path in [
        source_root / "docs" / "STACK.md",
        source_root / "scripts" / "phase-gate.sh",
    ]:
        if not required_path.exists():
            errors.append(f"Required template path is missing: {required_path}")

    gate_payload = manifest_payload.get("gate")
    if isinstance(gate_payload, dict):
        helper_script = gate_payload.get("helper_script")
        if isinstance(helper_script, str) and helper_script:
            gate_script_path = source_root / helper_script
            if not gate_script_path.exists():
                errors.append(f"Manifest gate helper script is missing: {gate_script_path}")
        stack_docs = gate_payload.get("stack_docs")
        if isinstance(stack_docs, str) and stack_docs:
            stack_docs_path = source_root / stack_docs
            if not stack_docs_path.exists():
                errors.append(f"Manifest gate stack docs are missing: {stack_docs_path}")
    else:
        warnings.append("Template manifest does not declare a `gate` section.")

    smoke_payload = manifest_payload.get("smoke")
    if isinstance(smoke_payload, dict):
        docs_anchor = smoke_payload.get("docs_anchor")
        if isinstance(docs_anchor, str) and docs_anchor:
            docs_path = source_root / parse_docs_anchor_target(docs_anchor)
            if not docs_path.exists():
                errors.append(f"Manifest smoke docs target is missing: {docs_path}")
    else:
        warnings.append("Template manifest does not declare a `smoke` section.")

    for hook in manifest.init_hooks:
        hook_id = str(hook.get("id", "unnamed-hook"))
        hook_kind = str(hook.get("kind", ""))
        if hook_kind != "script":
            warnings.append(
                f"Init hook `{hook_id}` uses unsupported kind {hook_kind!r}; only `script` is validated in this slice."
            )
            continue
        hook_path_value = hook.get("path")
        if not isinstance(hook_path_value, str) or not hook_path_value:
            errors.append(f"Init hook `{hook_id}` is missing a non-empty `path`.")
            continue
        hook_path = source_root / hook_path_value
        if not hook_path.exists():
            errors.append(f"Init hook `{hook_id}` points to a missing path: {hook_path}")

    if (source_root / "scripts" / "init-project.sh").exists():
        warnings.append(
            "Legacy compatibility script `scripts/init-project.sh` is present. "
            "Prefer CLI-native bootstrap via `sdd init` / `sdd integrate --apply-template-init`."
        )

    return errors, warnings


def release_status_payload(template: str) -> dict[str, Any]:
    manifest = load_template_manifest(template)
    provenance = detect_repo_provenance()
    workflow_version = normalize_release_version(load_repo_package_version())
    template_version = normalize_release_version(manifest.version)
    workflow_prefix = "workflow/"
    template_prefix = f"template/{manifest.template_id}/"
    workflow_tag = f"{workflow_prefix}{workflow_version}"
    template_tag = f"{template_prefix}{template_version}"
    workflow_tags = release_tags_for_prefix(workflow_prefix)
    template_tags = release_tags_for_prefix(template_prefix)
    template_errors, template_warnings = validate_template_manifest_paths(manifest)

    return {
        "status": "release-status",
        "repository": {
            "root": str(repo_root()),
            "head": provenance["revision"],
            "describe": provenance["describe"],
            "dirty": repo_is_dirty(),
        },
        "workflow": {
            "workspace_version": workflow_version,
            "expected_tag": workflow_tag,
            "expected_tag_exists": workflow_tag in workflow_tags,
            "latest_tag": latest_release_tag(workflow_tags, workflow_prefix) if workflow_tags else None,
            "latest_version": latest_release_version(workflow_prefix),
            "project_files_dir": str(derived_project_templates_dir()),
            "playbook_dir": str(canonical_playbook_dir()),
        },
        "template": {
            "id": manifest.template_id,
            "display_name": manifest.display_name,
            "workspace_version": template_version,
            "expected_tag": template_tag,
            "expected_tag_exists": template_tag in template_tags,
            "latest_tag": latest_release_tag(template_tags, template_prefix) if template_tags else None,
            "latest_version": latest_release_version(template_prefix),
            "manifest_path": str(manifest.manifest_path),
            "source_dir": str(manifest.source_dir),
            "source_dir_exists": manifest.source_dir.is_dir(),
            "path_errors": template_errors,
            "path_warnings": template_warnings,
        },
    }


def validate_release_payload(
    *,
    template: str,
    scope: Literal["all", "workflow", "template"],
    workflow_version: str | None,
    template_version: str | None,
    allow_existing_tags: bool,
    check_tags: bool,
) -> dict[str, Any]:
    manifest = load_template_manifest(template)
    workspace_workflow_version: str | None = None
    workflow_version_error: str | None = None
    try:
        workspace_workflow_version = normalize_release_version(load_repo_package_version())
    except typer.BadParameter as exc:
        workflow_version_error = str(exc)

    if scope in {"all", "workflow"} and workflow_version_error is not None:
        raise typer.BadParameter(workflow_version_error)

    effective_workflow_version = (
        normalize_release_version(workflow_version) if workflow_version else workspace_workflow_version
    )
    effective_template_version = normalize_release_version(template_version or manifest.version)
    workflow_tag = f"workflow/{effective_workflow_version}" if effective_workflow_version else None
    template_tag = f"template/{manifest.template_id}/{effective_template_version}"
    workflow_tags = release_tags_for_prefix("workflow/")
    template_tags = release_tags_for_prefix(f"template/{manifest.template_id}/")

    errors: list[str] = []
    warnings: list[str] = []

    if (
        workspace_workflow_version is not None
        and effective_workflow_version is not None
        and workspace_workflow_version != effective_workflow_version
    ):
        warnings.append("Requested workflow release version does not match `pyproject.toml` `project.version`.")
    if workspace_workflow_version is None and scope == "template":
        warnings.append("Workflow package version could not be resolved; template-scope validation continued.")
    if normalize_release_version(manifest.version) != effective_template_version:
        warnings.append("Requested template release version does not match `template.yaml` `version`.")

    if scope in {"all", "workflow"}:
        if not (derived_project_templates_dir() / "AGENTS.md.template").exists():
            errors.append("Missing workflow/project-files/AGENTS.md.template.")
        if not (derived_project_templates_dir() / "CLAUDE.md.template").exists():
            errors.append("Missing workflow/project-files/CLAUDE.md.template.")
        if not canonical_playbook_dir().is_dir():
            errors.append("Missing workflow/docs/playbooks/.")

    if scope in {"all", "template"}:
        template_errors, template_warnings = validate_template_manifest_paths(manifest)
        errors.extend(template_errors)
        warnings.extend(template_warnings)

    workflow_tag_exists = workflow_tag in workflow_tags if workflow_tag else None
    template_tag_exists = template_tag in template_tags
    if check_tags:
        if allow_existing_tags:
            if scope in {"all", "workflow"} and not workflow_tag_exists:
                errors.append(f"Expected workflow release tag does not exist: {workflow_tag}")
            if scope in {"all", "template"} and not template_tag_exists:
                errors.append(f"Expected template release tag does not exist: {template_tag}")
        else:
            if scope in {"all", "workflow"} and workflow_tag_exists:
                errors.append(f"Workflow release tag already exists: {workflow_tag}")
            if scope in {"all", "template"} and template_tag_exists:
                errors.append(f"Template release tag already exists: {template_tag}")
    else:
        warnings.append("Release tag existence checks were skipped; this validates structure only.")

    return {
        "status": "release-validation",
        "ok": not errors,
        "scope": scope,
        "template": manifest.template_id,
        "workflow": {
            "version": effective_workflow_version,
            "tag": workflow_tag,
            "tag_exists": workflow_tag_exists,
        },
        "template_release": {
            "version": effective_template_version,
            "tag": template_tag,
            "tag_exists": template_tag_exists,
        },
        "tag_policy": ("existing" if check_tags and allow_existing_tags else "new" if check_tags else "ignore"),
        "errors": errors,
        "warnings": warnings,
        "message": (
            "Release inputs are structurally valid." if not errors else "Release validation found blocking issues."
        ),
    }


def copy_directory_contents_in_place(source: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for item in source.iterdir():
        if item.name in IGNORE_NAMES:
            continue
        target = destination / item.name
        if item.is_dir():
            shutil.copytree(item, target, ignore=shutil.ignore_patterns(*sorted(IGNORE_NAMES)))
        else:
            shutil.copy2(item, target)


def resolve_upgrade_target(
    *,
    source_mode: str,
    scope: str,
    requested_targets: list[str],
    current_manifest: TemplateManifest,
    origin_payload: dict[str, Any],
    lock_payload: dict[str, Any],
) -> ResolvedUpgradeTarget:
    if source_mode == "workspace-current":
        requested = resolve_requested_versions(requested_targets)
        if requested:
            raise typer.BadParameter(
                "`--to` targets require `--source released-artifact`. "
                "Workspace-current mode always resolves from the current checkout."
            )
        provenance = detect_repo_provenance()
        return ResolvedUpgradeTarget(
            resolution="workspace-current",
            workflow_version=provenance["describe"],
            template_version=current_manifest.version,
            manifest=current_manifest,
            workflow_source="workspace-current",
            template_source="workspace-current",
        )

    if source_mode != "released-artifact":
        raise typer.BadParameter(
            f"Unsupported upgrade source mode: {source_mode}. Use `released-artifact` or `workspace-current`."
        )

    requested = resolve_requested_versions(requested_targets)
    installed_template_id = str(origin_payload.get("template", {}).get("id", current_manifest.template_id))
    template_request = requested.get("template")
    requested_template_id = template_request["id"] if template_request else installed_template_id
    if requested_template_id != installed_template_id:
        raise typer.BadParameter("Template upgrades must target the template already installed in the project.")

    installed_workflow_version = str(lock_payload.get("workflow", {}).get("version", ""))
    installed_template_version = str(lock_payload.get("template", {}).get("version", ""))
    if scope == "workflow" and template_request is not None:
        raise typer.BadParameter("`--to template@...` is not valid with `sdd upgrade workflow`.")
    if scope == "template" and "workflow" in requested:
        raise typer.BadParameter("`--to workflow@...` is not valid with `sdd upgrade template`.")

    if scope == "all":
        workflow_version = requested.get("workflow")
        template_version = template_request["version"] if template_request else None
        workflow_tag = resolve_release_tag("workflow/", workflow_version)
        template_tag = resolve_release_tag(f"template/{installed_template_id}/", template_version)
        manifest = load_release_template_manifest(installed_template_id, template_tag)
        return ResolvedUpgradeTarget(
            resolution="released-artifact",
            workflow_version=workflow_tag.removeprefix("workflow/"),
            template_version=template_tag.removeprefix(f"template/{installed_template_id}/"),
            manifest=manifest,
            workflow_source="released-artifact",
            template_source="released-artifact",
            workflow_tag=workflow_tag,
            template_tag=template_tag,
        )
    elif scope == "workflow":
        workflow_version = requested.get("workflow")
        workflow_tag = resolve_release_tag("workflow/", workflow_version)
        return ResolvedUpgradeTarget(
            resolution="released-artifact",
            workflow_version=workflow_tag.removeprefix("workflow/"),
            template_version=installed_template_version,
            manifest=current_manifest,
            workflow_source="released-artifact",
            template_source="workspace-current",
            workflow_tag=workflow_tag,
        )
    else:
        template_version = template_request["version"] if template_request else None
        template_tag = resolve_release_tag(f"template/{installed_template_id}/", template_version)
        manifest = load_release_template_manifest(installed_template_id, template_tag)
        return ResolvedUpgradeTarget(
            resolution="released-artifact",
            workflow_version=installed_workflow_version,
            template_version=template_tag.removeprefix(f"template/{installed_template_id}/"),
            manifest=manifest,
            workflow_source="workspace-current",
            template_source="released-artifact",
            template_tag=template_tag,
        )


def component_for_ownership(ownership: str) -> str | None:
    if ownership == "workflow-managed":
        return "workflow"
    if ownership in {"template-managed", "merge-required"}:
        return "template"
    return None


def build_upgrade_target_snapshot(
    target: ResolvedUpgradeTarget,
    project_slug: str,
) -> tuple[tempfile.TemporaryDirectory[str], Path]:
    temp_dir = tempfile.TemporaryDirectory(prefix="sdd-upgrade-target-")
    snapshot_root = Path(temp_dir.name)
    if target.workflow_source == "workspace-current":
        shutil.copytree(repo_root() / "workflow", snapshot_root / "workflow")
    else:
        assert target.workflow_tag is not None
        extract_git_tree(target.workflow_tag, "workflow", snapshot_root)

    if target.template_source == "workspace-current":
        copy_directory_contents_in_place(target.manifest.source_dir, snapshot_root)
    else:
        assert target.template_tag is not None
        template_extract_root = snapshot_root / ".sdd-template-extract"
        extract_git_tree(
            target.template_tag,
            f"templates/{target.manifest.template_id}/source",
            template_extract_root,
        )
        extracted_source = template_extract_root / "templates" / target.manifest.template_id / "source"
        if not extracted_source.is_dir():
            raise typer.BadParameter(f"Template source directory is missing from release tag {target.template_tag}.")
        copy_directory_contents_in_place(extracted_source, snapshot_root)
        shutil.rmtree(template_extract_root)
    write_workflow_project_files(
        snapshot_root,
        project_slug,
        project_files_source=snapshot_root / "workflow" / "project-files",
    )
    return temp_dir, snapshot_root


def maybe_normalize_installed_release(version: str) -> str | None:
    if not version:
        return None
    try:
        normalized = normalize_release_version(version)
        parse_release_semver(normalized)
    except typer.BadParameter:
        return None
    return normalized


def required_components_for_scope(scope: str) -> set[str]:
    if scope == "workflow":
        return {"workflow"}
    if scope == "template":
        return {"template"}
    return {"workflow", "template"}


def compatibility_window_fallback_allowed(
    *,
    component: str,
    source_mode: str,
    installed_version: str | None,
    current_manifest: TemplateManifest,
) -> bool:
    if source_mode != "workspace-current":
        return False
    if installed_version is None:
        # Workspace-current mode is an explicit maintainer/debug path and may carry
        # non-release lock coordinates (for example git describe strings).
        return True
    if component == "workflow":
        return installed_version == normalize_release_version(load_repo_package_version())
    return installed_version == normalize_release_version(current_manifest.version)


def validate_installed_baseline_reconstruction_policy(
    *,
    scope: str,
    source_mode: str,
    current_manifest: TemplateManifest,
    lock_payload: dict[str, Any],
) -> None:
    required_components = required_components_for_scope(scope)
    issues: list[str] = []
    workflow_tags = set(release_tags_for_prefix("workflow/"))
    template_prefix = f"template/{current_manifest.template_id}/"
    template_tags = set(release_tags_for_prefix(template_prefix))
    for component in sorted(required_components):
        if component == "workflow":
            prefix = "workflow/"
            available_tags = workflow_tags
        else:
            prefix = template_prefix
            available_tags = template_tags
        installed_raw = str(lock_payload.get(component, {}).get("version", ""))
        installed_version = maybe_normalize_installed_release(installed_raw)
        expected_tag = f"{prefix}{installed_version}" if installed_version is not None else None
        tag_available = expected_tag is not None and expected_tag in available_tags
        if tag_available:
            continue
        fallback_allowed = compatibility_window_fallback_allowed(
            component=component,
            source_mode=source_mode,
            installed_version=installed_version,
            current_manifest=current_manifest,
        )
        if fallback_allowed:
            continue
        if installed_version is None:
            issues.append(
                f"{component}: installed version {installed_raw!r} is not a valid release version "
                "(expected semantic style like v1.2.3)."
            )
            continue
        if expected_tag is None:
            issues.append(
                f"{component}: could not compute expected release tag from installed version {installed_version!r}."
            )
            continue
        if not available_tags:
            issues.append(
                f"{component}: expected installed release tag {expected_tag} is unavailable because no tags exist "
                f"under {prefix}."
            )
            continue
        issues.append(f"{component}: expected installed release tag {expected_tag} is unavailable in this checkout.")
    if not issues:
        return
    remediation = (
        "Restore access to the missing installed component release tags, or run "
        "`sdd upgrade --source workspace-current ...` from a checkout whose workflow/template versions match "
        "the installed project lock versions."
    )
    raise typer.BadParameter(
        "Installed baseline cannot be reconstructed from released artifacts for the required upgrade scope. "
        + " ".join(issues)
        + " This project is outside the supported compatibility window. "
        + remediation
    )


def build_installed_baseline_snapshot(
    current_manifest: TemplateManifest,
    lock_payload: dict[str, Any],
    project_slug: str,
    scope: str,
    source_mode: str,
) -> tuple[tempfile.TemporaryDirectory[str], Path]:
    temp_dir = tempfile.TemporaryDirectory(prefix="sdd-upgrade-baseline-")
    snapshot_root = Path(temp_dir.name)

    validate_installed_baseline_reconstruction_policy(
        scope=scope,
        source_mode=source_mode,
        current_manifest=current_manifest,
        lock_payload=lock_payload,
    )

    installed_workflow_version = maybe_normalize_installed_release(
        str(lock_payload.get("workflow", {}).get("version", ""))
    )
    installed_template_version = maybe_normalize_installed_release(
        str(lock_payload.get("template", {}).get("version", ""))
    )

    workflow_tag = (
        f"workflow/{installed_workflow_version}"
        if installed_workflow_version
        and f"workflow/{installed_workflow_version}" in release_tags_for_prefix("workflow/")
        else None
    )
    template_tag = (
        f"template/{current_manifest.template_id}/{installed_template_version}"
        if installed_template_version
        and f"template/{current_manifest.template_id}/{installed_template_version}"
        in release_tags_for_prefix(f"template/{current_manifest.template_id}/")
        else None
    )

    if workflow_tag is not None:
        extract_git_tree(workflow_tag, "workflow", snapshot_root)
    else:
        shutil.copytree(repo_root() / "workflow", snapshot_root / "workflow")

    if template_tag is not None:
        template_extract_root = snapshot_root / ".sdd-template-extract"
        extract_git_tree(
            template_tag,
            f"templates/{current_manifest.template_id}/source",
            template_extract_root,
        )
        extracted_source = template_extract_root / "templates" / current_manifest.template_id / "source"
        if not extracted_source.is_dir():
            raise typer.BadParameter(f"Template source directory is missing from release tag {template_tag}.")
        copy_directory_contents_in_place(extracted_source, snapshot_root)
        shutil.rmtree(template_extract_root)
    else:
        copy_directory_contents_in_place(current_manifest.source_dir, snapshot_root)

    write_workflow_project_files(
        snapshot_root,
        project_slug,
        project_files_source=snapshot_root / "workflow" / "project-files",
    )
    return temp_dir, snapshot_root


def is_text_file(path: Path) -> bool:
    data = path.read_bytes()
    if b"\x00" in data:
        return False
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True


def try_clean_text_merge(base_path: Path, local_path: Path, target_path: Path) -> tuple[bool, str | None]:
    if not (is_text_file(base_path) and is_text_file(local_path) and is_text_file(target_path)):
        return False, None

    result = subprocess.run(
        ["git", "merge-file", "-p", str(local_path), str(base_path), str(target_path)],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode == 0:
        return True, result.stdout
    if result.returncode == 1:
        return False, None
    raise typer.BadParameter(f"git merge-file failed while analyzing {local_path.name}: {result.stderr.strip()}")


def maybe_promote_entry_to_auto_merge(
    entry: UpgradeEntry,
    path: str,
    ownership: str,
    baseline_hash: str | None,
    baseline_files: dict[str, Path],
    local_files: dict[str, Path],
    target_files: dict[str, Path],
) -> tuple[UpgradeEntry, str | None]:
    if entry.action != "merge-required" or ownership == "merge-required":
        return entry, None

    baseline_file = baseline_files.get(path)
    local_file = local_files.get(path)
    target_file = target_files.get(path)
    if baseline_file is None or local_file is None or target_file is None or baseline_hash is None:
        return entry, None
    if sha256_file(baseline_file) != baseline_hash:
        return entry, None

    merged_cleanly, merged_content = try_clean_text_merge(
        base_path=baseline_file,
        local_path=local_file,
        target_path=target_file,
    )
    if not merged_cleanly or merged_content is None:
        return entry, None

    return (
        UpgradeEntry(
            path=entry.path,
            ownership=entry.ownership,
            action="auto-merge",
            reason=("Local and upstream target both changed, but a clean three-way text merge was possible."),
            local_exists=entry.local_exists,
            target_exists=entry.target_exists,
            baseline_present=entry.baseline_present,
        ),
        merged_content,
    )


def scope_includes_category(scope: str, ownership: str) -> bool:
    if scope == "all":
        return ownership in {"workflow-managed", "template-managed", "merge-required"}
    if scope == "workflow":
        return ownership == "workflow-managed"
    if scope == "template":
        return ownership in {"template-managed", "merge-required"}
    raise typer.BadParameter(f"Unsupported upgrade scope: {scope}")


def baseline_hashes_for_scope(lock_payload: dict[str, Any], scope: str) -> dict[str, str]:
    workflow_hashes = dict(lock_payload.get("workflow", {}).get("baseline_hashes", {}))
    template_hashes = dict(lock_payload.get("template", {}).get("baseline_hashes", {}))
    if scope == "workflow":
        return workflow_hashes
    if scope == "template":
        return template_hashes
    if scope == "all":
        return {**workflow_hashes, **template_hashes}
    raise typer.BadParameter(f"Unsupported upgrade scope: {scope}")


def validate_reconstructed_baseline_integrity(
    baseline_hashes: dict[str, str],
    baseline_files: dict[str, Path],
    rules: OwnershipRules,
    scope: str,
) -> None:
    missing_paths: list[str] = []
    mismatched_hashes: list[tuple[str, str, str]] = []

    for path, recorded_hash in sorted(baseline_hashes.items()):
        ownership = classify_path(path, rules)
        if not scope_includes_category(scope, ownership):
            continue
        baseline_file = baseline_files.get(path)
        if baseline_file is None:
            missing_paths.append(path)
            continue
        reconstructed_hash = sha256_file(baseline_file)
        if reconstructed_hash != recorded_hash:
            mismatched_hashes.append((path, recorded_hash, reconstructed_hash))

    if not missing_paths and not mismatched_hashes:
        return

    details: list[str] = []
    if missing_paths:
        details.append(f"missing paths: {', '.join(missing_paths)}")
    if mismatched_hashes:
        details.append(
            "hash mismatches: "
            + ", ".join(
                f"{path} (recorded={recorded}, reconstructed={reconstructed})"
                for path, recorded, reconstructed in mismatched_hashes
            )
        )
    raise typer.BadParameter(
        "Installed baseline integrity check failed for `.sdd-lock.yaml` baseline metadata. "
        + "; ".join(details)
        + " This usually indicates metadata corruption or a compatibility-window mismatch."
    )


def build_upgrade_candidate_paths(
    local_root: Path,
    target_root: Path,
    rules: OwnershipRules,
    scope: str,
    baseline_hashes: dict[str, str],
) -> list[str]:
    local_files = collect_files(local_root)
    target_files = collect_files(target_root)
    candidate_paths: set[str] = set(baseline_hashes)
    for path in set(local_files) | set(target_files):
        ownership = classify_path(path, rules)
        if scope_includes_category(scope, ownership):
            candidate_paths.add(path)
    return sorted(candidate_paths)


def classify_upgrade_entry(
    path: str,
    ownership: str,
    baseline_hash: str | None,
    local_hash: str | None,
    target_hash: str | None,
) -> UpgradeEntry:
    baseline_present = baseline_hash is not None
    local_exists = local_hash is not None
    target_exists = target_hash is not None

    if ownership == "user-owned":
        return UpgradeEntry(
            path=path,
            ownership=ownership,
            action="blocked-user-owned",
            reason="Path is user-owned and excluded from automatic upgrade planning.",
            local_exists=local_exists,
            target_exists=target_exists,
            baseline_present=baseline_present,
        )

    if not baseline_present and not target_exists:
        return UpgradeEntry(
            path=path,
            ownership=ownership,
            action="untracked",
            reason="No installed baseline or current target file exists for this path.",
            local_exists=local_exists,
            target_exists=target_exists,
            baseline_present=False,
        )

    if not baseline_present and target_exists:
        if not local_exists:
            action = "merge-required" if ownership == "merge-required" else "auto-add"
            reason = (
                "Managed file is new in the current target and absent locally."
                if action == "auto-add"
                else "Path is merge-required and new upstream content must be reviewed."
            )
        elif local_hash == target_hash:
            action = "already-matches-target"
            reason = "Local file already matches the current target content."
        else:
            action = "merge-required"
            reason = "Managed file is new upstream, but a conflicting local file already exists."
        return UpgradeEntry(
            path=path,
            ownership=ownership,
            action=action,
            reason=reason,
            local_exists=local_exists,
            target_exists=True,
            baseline_present=False,
        )

    if baseline_present and not target_exists:
        if not local_exists:
            return UpgradeEntry(
                path=path,
                ownership=ownership,
                action="already-absent",
                reason="Managed file was removed upstream and is already absent locally.",
                local_exists=False,
                target_exists=False,
                baseline_present=True,
            )
        if local_hash == baseline_hash and ownership != "merge-required":
            return UpgradeEntry(
                path=path,
                ownership=ownership,
                action="auto-delete",
                reason="Managed file was removed upstream and local content still matches baseline.",
                local_exists=True,
                target_exists=False,
                baseline_present=True,
            )
        return UpgradeEntry(
            path=path,
            ownership=ownership,
            action="merge-required",
            reason="Managed file was removed upstream, but local content no longer matches baseline.",
            local_exists=True,
            target_exists=False,
            baseline_present=True,
        )

    if local_exists and target_exists and local_hash == target_hash == baseline_hash:
        return UpgradeEntry(
            path=path,
            ownership=ownership,
            action="unchanged",
            reason="Local file already matches both installed baseline and current target.",
            local_exists=True,
            target_exists=True,
            baseline_present=True,
        )

    if local_exists and target_exists and local_hash == target_hash:
        return UpgradeEntry(
            path=path,
            ownership=ownership,
            action="already-matches-target",
            reason="Local file already matches the current target content.",
            local_exists=True,
            target_exists=True,
            baseline_present=True,
        )

    if local_hash == baseline_hash and target_hash != baseline_hash:
        action = "merge-required" if ownership == "merge-required" else "auto-update"
        reason = (
            "Installed file still matches baseline, so the current target can replace it safely."
            if action == "auto-update"
            else "Path is merge-required, so upstream changes require explicit review."
        )
        return UpgradeEntry(
            path=path,
            ownership=ownership,
            action=action,
            reason=reason,
            local_exists=local_exists,
            target_exists=target_exists,
            baseline_present=True,
        )

    if local_hash != baseline_hash and target_hash == baseline_hash:
        return UpgradeEntry(
            path=path,
            ownership=ownership,
            action="keep-local",
            reason="Local file changed since installation while upstream target stayed at baseline.",
            local_exists=local_exists,
            target_exists=target_exists,
            baseline_present=True,
        )

    return UpgradeEntry(
        path=path,
        ownership=ownership,
        action="merge-required",
        reason="Local and upstream target both differ from the installed baseline.",
        local_exists=local_exists,
        target_exists=target_exists,
        baseline_present=True,
    )


def analyze_upgrade(
    project_root: Path,
    target: ResolvedUpgradeTarget,
    project_slug: str,
    current_manifest: TemplateManifest,
    rules: OwnershipRules,
    lock_payload: dict[str, Any],
    scope: str,
) -> UpgradeAnalysis:
    temp_dir, target_root = build_upgrade_target_snapshot(target, project_slug)
    baseline_temp_dir, baseline_root = build_installed_baseline_snapshot(
        current_manifest=current_manifest,
        lock_payload=lock_payload,
        project_slug=project_slug,
        scope=scope,
        source_mode=target.resolution,
    )
    try:
        local_files = collect_files(project_root)
        target_files = collect_files(target_root)
        baseline_files = collect_files(baseline_root)
        target_hashes = {path: sha256_file(abs_path) for path, abs_path in target_files.items()}
        baseline_hashes = baseline_hashes_for_scope(lock_payload, scope)
        validate_reconstructed_baseline_integrity(
            baseline_hashes=baseline_hashes,
            baseline_files=baseline_files,
            rules=rules,
            scope=scope,
        )
        candidate_paths = build_upgrade_candidate_paths(project_root, target_root, rules, scope, baseline_hashes)
        entries: list[UpgradeEntry] = []
        merged_contents: dict[str, str] = {}
        for path in candidate_paths:
            ownership = classify_path(path, rules)
            if not scope_includes_category(scope, ownership):
                continue
            local_file = local_files.get(path)
            target_file = target_files.get(path)
            entry = classify_upgrade_entry(
                path=path,
                ownership=ownership,
                baseline_hash=baseline_hashes.get(path),
                local_hash=sha256_file(local_file) if local_file else None,
                target_hash=sha256_file(target_file) if target_file else None,
            )
            entry, merged_content = maybe_promote_entry_to_auto_merge(
                entry=entry,
                path=path,
                ownership=ownership,
                baseline_hash=baseline_hashes.get(path),
                baseline_files=baseline_files,
                local_files=local_files,
                target_files=target_files,
            )
            if merged_content is not None:
                merged_contents[path] = merged_content
            entries.append(entry)
    finally:
        temp_dir.cleanup()
        baseline_temp_dir.cleanup()

    return UpgradeAnalysis(
        entries=entries,
        target_hashes=target_hashes,
        target_versions={
            "workflow": target.workflow_version,
            "template": target.template_version,
        },
        merged_contents=merged_contents,
    )


def summarize_upgrade_entries(entries: list[UpgradeEntry]) -> dict[str, int]:
    actionable_actions = {"auto-add", "auto-update", "auto-delete", "auto-merge", "merge-required"}
    return {
        "paths_considered": len(entries),
        "actionable_paths": sum(1 for entry in entries if entry.action in actionable_actions),
        "auto_add": sum(1 for entry in entries if entry.action == "auto-add"),
        "auto_update": sum(1 for entry in entries if entry.action == "auto-update"),
        "auto_delete": sum(1 for entry in entries if entry.action == "auto-delete"),
        "auto_merge": sum(1 for entry in entries if entry.action == "auto-merge"),
        "keep_local": sum(1 for entry in entries if entry.action == "keep-local"),
        "merge_required": sum(1 for entry in entries if entry.action == "merge-required"),
        "unchanged": sum(1 for entry in entries if entry.action == "unchanged"),
        "already_matches_target": sum(1 for entry in entries if entry.action == "already-matches-target"),
        "already_absent": sum(1 for entry in entries if entry.action == "already-absent"),
    }


def build_upgrade_plan(
    project_root: Path,
    target: ResolvedUpgradeTarget,
    project_slug: str,
    current_manifest: TemplateManifest,
    rules: OwnershipRules,
    lock_payload: dict[str, Any],
    scope: str,
) -> dict[str, Any]:
    analysis = analyze_upgrade(
        project_root=project_root,
        target=target,
        project_slug=project_slug,
        current_manifest=current_manifest,
        rules=rules,
        lock_payload=lock_payload,
        scope=scope,
    )
    return {
        "status": "upgrade-plan",
        "mode": "check",
        "resolution": target.resolution,
        "scope": scope,
        "project": str(project_root.resolve()),
        "template": target.manifest.template_id,
        "project_name": project_slug,
        "installed": {
            "workflow": lock_payload.get("workflow", {}).get("version"),
            "template": lock_payload.get("template", {}).get("version"),
        },
        "target": analysis.target_versions,
        "summary": summarize_upgrade_entries(analysis.entries),
        "entries": [
            {
                "path": entry.path,
                "ownership": entry.ownership,
                "action": entry.action,
                "reason": entry.reason,
                "local_exists": entry.local_exists,
                "target_exists": entry.target_exists,
                "baseline_present": entry.baseline_present,
            }
            for entry in analysis.entries
        ],
        "message": ("Check mode only. Review the plan before applying managed-file changes."),
    }


def backup_paths(project_root: Path, relative_paths: list[str], backup_root: Path) -> dict[str, bool]:
    existed: dict[str, bool] = {}
    for rel_path in relative_paths:
        source = project_root / rel_path
        existed[rel_path] = source.exists()
        if source.exists():
            backup_path = backup_root / rel_path
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, backup_path)
    return existed


def restore_paths_from_backup(project_root: Path, backup_root: Path, existed: dict[str, bool]) -> None:
    for rel_path, was_present in existed.items():
        target = project_root / rel_path
        backup_path = backup_root / rel_path
        if was_present:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(backup_path, target)
            continue
        if target.exists():
            target.unlink()


def update_lock_payload_for_apply(
    lock_payload: dict[str, Any],
    entries: list[UpgradeEntry],
    target_hashes: dict[str, str],
    target_versions: dict[str, str],
    scope: str,
) -> dict[str, Any]:
    updated = dict(lock_payload)
    updated["project_metadata_version"] = METADATA_SCHEMA_VERSION
    updated["generated_at"] = utc_timestamp()

    workflow_section = dict(updated.get("workflow", {}))
    template_section = dict(updated.get("template", {}))
    workflow_hashes = dict(workflow_section.get("baseline_hashes", {}))
    template_hashes = dict(template_section.get("baseline_hashes", {}))

    safe_actions = {"auto-add", "auto-update", "auto-delete", "auto-merge"}
    for entry in entries:
        if entry.action not in safe_actions:
            continue
        component = component_for_ownership(entry.ownership)
        if component == "workflow":
            hashes = workflow_hashes
        elif component == "template":
            hashes = template_hashes
        else:
            continue

        if entry.action == "auto-delete":
            hashes.pop(entry.path, None)
        else:
            target_hash = target_hashes.get(entry.path)
            if target_hash is not None:
                hashes[entry.path] = target_hash

    workflow_section["baseline_hashes"] = workflow_hashes
    template_section["baseline_hashes"] = template_hashes

    for component in ("workflow", "template"):
        if scope != "all" and component != scope:
            continue
        blockers = [
            entry.path
            for entry in entries
            if component_for_ownership(entry.ownership) == component and entry.action == "merge-required"
        ]
        section = workflow_section if component == "workflow" else template_section
        if blockers:
            section["pending_version"] = target_versions[component]
            section["pending_paths"] = blockers
        else:
            section["version"] = target_versions[component]
            section.pop("pending_version", None)
            section.pop("pending_paths", None)

    updated["workflow"] = workflow_section
    updated["template"] = template_section
    return updated


def apply_upgrade(
    project_root: Path,
    target: ResolvedUpgradeTarget,
    project_slug: str,
    current_manifest: TemplateManifest,
    rules: OwnershipRules,
    lock_payload: dict[str, Any],
    scope: str,
) -> dict[str, Any]:
    analysis = analyze_upgrade(
        project_root=project_root,
        target=target,
        project_slug=project_slug,
        current_manifest=current_manifest,
        rules=rules,
        lock_payload=lock_payload,
        scope=scope,
    )
    entries = analysis.entries
    safe_actions = {"auto-add", "auto-update", "auto-delete", "auto-merge"}
    safe_entries = [entry for entry in entries if entry.action in safe_actions]
    merge_entries = [entry for entry in entries if entry.action == "merge-required"]
    keep_local_entries = [entry for entry in entries if entry.action == "keep-local"]

    if not safe_entries:
        status = "upgrade-partial" if merge_entries else "upgrade-noop"
        if merge_entries:
            updated_lock = update_lock_payload_for_apply(
                lock_payload=lock_payload,
                entries=entries,
                target_hashes=analysis.target_hashes,
                target_versions=analysis.target_versions,
                scope=scope,
            )
            write_yaml(project_root / ".sdd-lock.yaml", updated_lock)
        return {
            "status": status,
            "mode": "apply",
            "resolution": target.resolution,
            "scope": scope,
            "project": str(project_root.resolve()),
            "template": target.manifest.template_id,
            "project_name": project_slug,
            "installed": {
                "workflow": lock_payload.get("workflow", {}).get("version"),
                "template": lock_payload.get("template", {}).get("version"),
            },
            "target": analysis.target_versions,
            "summary": summarize_upgrade_entries(entries),
            "applied": {"count": 0, "paths": []},
            "blocked": [entry.path for entry in merge_entries],
            "kept_local": [entry.path for entry in keep_local_entries],
            "entries": [
                {
                    "path": entry.path,
                    "ownership": entry.ownership,
                    "action": entry.action,
                    "reason": entry.reason,
                    "local_exists": entry.local_exists,
                    "target_exists": entry.target_exists,
                    "baseline_present": entry.baseline_present,
                }
                for entry in entries
            ],
            "message": (
                "No safe file operations were applied. Review merge-required paths before retrying."
                if merge_entries
                else "No managed file changes were necessary."
            ),
        }

    temp_dir, target_root = build_upgrade_target_snapshot(target, project_slug)
    try:
        managed_paths = sorted({entry.path for entry in safe_entries} | {".sdd-lock.yaml"})
        with tempfile.TemporaryDirectory(prefix="sdd-upgrade-backup-") as backup_dir:
            backup_root = Path(backup_dir)
            existed = backup_paths(project_root, managed_paths, backup_root)
            try:
                for entry in safe_entries:
                    destination = project_root / entry.path
                    if entry.action == "auto-delete":
                        if destination.exists():
                            destination.unlink()
                        continue

                    destination.parent.mkdir(parents=True, exist_ok=True)
                    if entry.action == "auto-merge":
                        merged_content = analysis.merged_contents.get(entry.path)
                        if merged_content is None:
                            raise typer.BadParameter(f"Merged content was not available for {entry.path}.")
                        destination.write_text(merged_content, encoding="utf-8")
                    else:
                        source = target_root / entry.path
                        shutil.copy2(source, destination)

                updated_lock = update_lock_payload_for_apply(
                    lock_payload=lock_payload,
                    entries=entries,
                    target_hashes=analysis.target_hashes,
                    target_versions=analysis.target_versions,
                    scope=scope,
                )
                write_yaml(project_root / ".sdd-lock.yaml", updated_lock)
            except Exception:
                restore_paths_from_backup(project_root, backup_root, existed)
                raise
    finally:
        temp_dir.cleanup()

    return {
        "status": "upgrade-partial" if merge_entries else "upgrade-applied",
        "mode": "apply",
        "resolution": target.resolution,
        "scope": scope,
        "project": str(project_root.resolve()),
        "template": target.manifest.template_id,
        "project_name": project_slug,
        "installed_before": {
            "workflow": lock_payload.get("workflow", {}).get("version"),
            "template": lock_payload.get("template", {}).get("version"),
        },
        "target": analysis.target_versions,
        "summary": summarize_upgrade_entries(entries),
        "applied": {
            "count": len(safe_entries),
            "paths": [entry.path for entry in safe_entries],
            "auto_add": sum(1 for entry in safe_entries if entry.action == "auto-add"),
            "auto_update": sum(1 for entry in safe_entries if entry.action == "auto-update"),
            "auto_delete": sum(1 for entry in safe_entries if entry.action == "auto-delete"),
            "auto_merge": sum(1 for entry in safe_entries if entry.action == "auto-merge"),
        },
        "blocked": [entry.path for entry in merge_entries],
        "kept_local": [entry.path for entry in keep_local_entries],
        "metadata_updated": [".sdd-lock.yaml"],
        "entries": [
            {
                "path": entry.path,
                "ownership": entry.ownership,
                "action": entry.action,
                "reason": entry.reason,
                "local_exists": entry.local_exists,
                "target_exists": entry.target_exists,
                "baseline_present": entry.baseline_present,
            }
            for entry in entries
        ],
        "message": (
            "Applied safe managed-file updates and refreshed lock metadata."
            if not merge_entries
            else "Applied safe managed-file updates, but some paths still require review."
        ),
    }


def run_compat_init_script(
    destination: Path,
    project_name: str,
    domain: str | None,
    admin_email: str,
) -> None:
    if not domain:
        raise typer.BadParameter("--domain is required with --run-compat-init.")
    script = destination / "scripts" / "init-project.sh"
    if not script.exists():
        typer.echo(
            f"Compatibility init script not found: {script}",
            err=True,
        )
        raise typer.Exit(code=1)
    result = subprocess.run(
        ["bash", str(script), project_name, domain, admin_email],
        cwd=destination,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        if result.stdout:
            typer.echo(result.stdout, err=True)
        if result.stderr:
            typer.echo(result.stderr, err=True)
        raise typer.Exit(result.returncode)
    if result.stdout:
        typer.echo(result.stdout.rstrip())


def sanitize_domain(value: str) -> str:
    domain = value.strip()
    domain = domain.removeprefix("http://").removeprefix("https://").rstrip("/")
    if not domain:
        raise typer.BadParameter("Domain cannot be empty.")
    if not re.fullmatch(r"[a-zA-Z0-9]([a-zA-Z0-9.-]*[a-zA-Z0-9])?", domain):
        raise typer.BadParameter(f"Domain must be a hostname without protocol (for example `example.com`): {value!r}")
    return domain


def looks_like_text_file(path: Path) -> bool:
    if path.name.startswith(".env"):
        return True
    text_suffixes = {
        ".css",
        ".conf",
        ".ini",
        ".js",
        ".json",
        ".md",
        ".py",
        ".sh",
        ".toml",
        ".ts",
        ".tsx",
        ".txt",
        ".vue",
        ".yaml",
        ".yml",
    }
    return path.suffix.lower() in text_suffixes


def replace_env_line(content: str, key: str, value: str) -> str:
    pattern = re.compile(rf"(?m)^{re.escape(key)}=.*$")
    replacement = f"{key}={value}"
    if pattern.search(content):
        return pattern.sub(replacement, content)
    suffix = "" if content.endswith("\n") or not content else "\n"
    return f"{content}{suffix}{replacement}\n"


def apply_template_bootstrap(
    destination: Path,
    project_slug: str,
    domain: str | None,
    admin_email: str,
) -> dict[str, Any]:
    project_display_name = slug_to_display_name(project_slug)
    db_name = project_slug.replace("-", "_")
    resolved_domain = sanitize_domain(domain) if domain else None

    replacements = {
        "[PROJECT_NAME]": project_display_name,
        "[PROJECT_DESCRIPTION]": f"{project_display_name} backend",
        "my-project": project_slug,
        "myapp": db_name,
    }
    if resolved_domain:
        replacements["[DOMAIN]"] = resolved_domain

    changed_paths: list[str] = []
    for rel_path, abs_path in collect_files(destination).items():
        if rel_path.startswith(("workflow/", ".sdd/")):
            continue
        if rel_path in {".sdd-origin.yaml", ".sdd-lock.yaml"}:
            continue
        if rel_path == "scripts/init-project.sh":
            continue
        if not looks_like_text_file(abs_path):
            continue
        try:
            original = abs_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        updated = original
        for source, target in replacements.items():
            updated = updated.replace(source, target)
        if updated != original:
            abs_path.write_text(updated, encoding="utf-8")
            changed_paths.append(rel_path)

    env_created = False
    env_path = destination / ".env"
    env_example_path = destination / ".env.example"
    if env_example_path.exists():
        env_content = env_example_path.read_text(encoding="utf-8")
        for source, target in replacements.items():
            env_content = env_content.replace(source, target)
        secret_key = secrets.token_hex(32)
        db_password = secrets.token_urlsafe(24)
        env_content = replace_env_line(env_content, "POSTGRES_PASSWORD", db_password)
        env_content = replace_env_line(
            env_content,
            "DATABASE_URL",
            f"postgresql+asyncpg://app_user:{db_password}@db:5432/{db_name}",
        )
        env_content = replace_env_line(env_content, "SECRET_KEY", secret_key)
        if resolved_domain:
            env_content = env_content.replace("[DOMAIN]", resolved_domain)
        env_path.write_text(env_content, encoding="utf-8")
        env_created = True
        if ".env" not in changed_paths:
            changed_paths.append(".env")

    migration_path = destination / "alembic" / "versions" / "0001_users_table.py"
    if admin_email != "admin@example.com" and migration_path.exists():
        migration_text = migration_path.read_text(encoding="utf-8")
        migration_updated = migration_text.replace("admin@example.com", admin_email)
        if migration_updated != migration_text:
            migration_path.write_text(migration_updated, encoding="utf-8")
            rel_migration_path = str(migration_path.relative_to(destination))
            if rel_migration_path not in changed_paths:
                changed_paths.append(rel_migration_path)

    return {
        "project_name": project_slug,
        "project_display_name": project_display_name,
        "database_name": db_name,
        "domain": resolved_domain,
        "admin_email": admin_email,
        "env_created": env_created,
        "changed_paths": sorted(changed_paths),
        "changed_count": len(changed_paths),
    }


def detect_repo_shape(target_dir: Path) -> dict[str, Any]:
    return {
        "path": str(target_dir.resolve()),
        "has_workflow_dir": (target_dir / "workflow").is_dir(),
        "has_docs_workflows_compat": (target_dir / "docs" / "workflows").is_dir(),
        "has_template_stack_docs": (target_dir / "docs" / "STACK.md").exists(),
        "has_agents_file": (target_dir / "AGENTS.md").exists(),
        "has_claude_file": (target_dir / "CLAUDE.md").exists(),
        "has_origin_metadata": (target_dir / ".sdd-origin.yaml").exists(),
        "has_lock_metadata": (target_dir / ".sdd-lock.yaml").exists(),
        "has_ownership_metadata": (metadata_dir(target_dir) / "ownership.yaml").exists(),
        "has_template_manifest_metadata": project_template_manifest_path(target_dir).exists(),
        "has_reference_backend": (target_dir / "app").is_dir(),
        "has_reference_frontend": (target_dir / "frontend").is_dir(),
    }


def collect_files(base: Path) -> dict[str, Path]:
    files: dict[str, Path] = {}
    for path in base.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(base)
        if any(part in IGNORE_NAMES for part in rel.parts):
            continue
        files[str(rel)] = path
    return files


def compare_snapshots(repo_dir: Path, dev_dir: Path) -> DiffSummary:
    repo_files = collect_files(repo_dir)
    dev_files = collect_files(dev_dir)
    changed: list[str] = []
    only_in_repo = sorted(set(repo_files) - set(dev_files))
    only_in_dev = sorted(set(dev_files) - set(repo_files))
    for rel in sorted(set(repo_files) & set(dev_files)):
        if not filecmp.cmp(repo_files[rel], dev_files[rel], shallow=False):
            changed.append(rel)
    return DiffSummary(changed=changed, only_in_repo=only_in_repo, only_in_dev=only_in_dev)


def classify_dev_workspace_path(template: str, relative_path: str, change_kind: str) -> dict[str, Any]:
    root = repo_root()
    if relative_path in {"AGENTS.md", "CLAUDE.md"}:
        authoritative_target = root / "workflow" / "project-files" / f"{relative_path}.template"
        return {
            "path": relative_path,
            "change_kind": change_kind,
            "classification": "generated-only",
            "owner": "generated-project-file",
            "status": "blocked",
            "reason": (
                f"{relative_path} in dev workspaces is a rendered project file, not an authoritative template source."
            ),
            "suggested_authoritative_target": str(authoritative_target),
        }
    if relative_path == ".sdd-dev-state.json" or relative_path.startswith(".sdd/"):
        return {
            "path": relative_path,
            "change_kind": change_kind,
            "classification": "generated-only",
            "owner": "dev-metadata",
            "status": "blocked",
            "reason": "Generated dev metadata must not be promoted back into canonical sources.",
            "suggested_authoritative_target": None,
        }

    if relative_path.startswith("workflow/"):
        authoritative_target = root / relative_path
        return {
            "path": relative_path,
            "change_kind": change_kind,
            "classification": "authoritative",
            "owner": "workflow",
            "status": "review",
            "reason": "Re-apply this change in the workflow-owned canonical source.",
            "suggested_authoritative_target": str(authoritative_target),
        }

    authoritative_target = root / "templates" / template / "source" / relative_path
    return {
        "path": relative_path,
        "change_kind": change_kind,
        "classification": "authoritative",
        "owner": "template",
        "status": "review",
        "reason": "Re-apply this change in the template-owned canonical source.",
        "suggested_authoritative_target": str(authoritative_target),
    }


def classify_dev_workspace_summary(template: str, summary: DiffSummary) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for path in summary.changed:
        entries.append(classify_dev_workspace_path(template, path, "modified"))
    for path in summary.only_in_repo:
        entries.append(classify_dev_workspace_path(template, path, "deleted-in-dev"))
    for path in summary.only_in_dev:
        entries.append(classify_dev_workspace_path(template, path, "added-in-dev"))
    entries.sort(key=lambda item: (item["classification"], item["owner"], item["path"]))
    return entries


def print_json(payload: dict[str, Any]) -> None:
    typer.echo(json.dumps(payload, indent=2, sort_keys=True))


def detect_backend_package_manager(source_root: Path) -> str | None:
    if (source_root / "uv.lock").exists():
        return "uv"
    if (source_root / "poetry.lock").exists():
        return "poetry"
    if (source_root / "requirements.txt").exists() or (source_root / "requirements-dev.txt").exists():
        return "pip"
    if (source_root / "pyproject.toml").exists():
        return "pyproject"
    return None


def detect_frontend_package_manager(frontend_root: Path) -> str | None:
    if (frontend_root / "pnpm-lock.yaml").exists():
        return "pnpm"
    if (frontend_root / "yarn.lock").exists():
        return "yarn"
    if (frontend_root / "package-lock.json").exists():
        return "npm"
    if (frontend_root / "bun.lockb").exists() or (frontend_root / "bun.lock").exists():
        return "bun"
    if (frontend_root / "package.json").exists():
        return "npm"
    return None


def load_json_file_if_exists(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        return None
    return payload


def package_json_names(frontend_root: Path) -> set[str]:
    package_payload = load_json_file_if_exists(frontend_root / "package.json") or {}
    names: set[str] = set()
    for section in ("dependencies", "devDependencies", "peerDependencies"):
        section_payload = package_payload.get(section)
        if isinstance(section_payload, dict):
            names.update(str(name) for name in section_payload.keys())
    return names


def infer_technologies(source_root: Path) -> list[str]:
    technologies: list[str] = []
    if (source_root / "pyproject.toml").exists():
        technologies.append("Python")

    backend_code = ""
    app_main = source_root / "app" / "main.py"
    if app_main.exists():
        backend_code = app_main.read_text(encoding="utf-8")
        if "FastAPI" in backend_code:
            technologies.append("FastAPI")

    if (source_root / "alembic.ini").exists():
        technologies.append("Alembic")

    if (source_root / "docker-compose.yml").exists():
        technologies.append("Docker Compose")

    compose_files = [
        source_root / "docker-compose.yml",
        source_root / "docker-compose.override.yml",
        source_root / "docker-compose.prod.yml",
        source_root / "docker-compose.ci.yml",
    ]
    compose_text = "\n".join(path.read_text(encoding="utf-8") for path in compose_files if path.exists())
    if "postgres" in compose_text.lower():
        technologies.append("PostgreSQL")

    frontend_root = source_root / "frontend"
    package_names = package_json_names(frontend_root)
    if "nuxt" in package_names or (frontend_root / "nuxt.config.ts").exists():
        technologies.append("Nuxt")
    if "react" in package_names:
        technologies.append("React")
    if "react-router" in package_names or "@react-router/dev" in package_names:
        technologies.append("React Router 7")
    if "vue" in package_names:
        technologies.append("Vue")
    if "vite" in package_names or (frontend_root / "vite.config.ts").exists():
        technologies.append("Vite")
    if "typescript" in package_names or (frontend_root / "tsconfig.json").exists():
        technologies.append("TypeScript")
    if "tailwindcss" in package_names or (frontend_root / "tailwind.config.ts").exists():
        technologies.append("Tailwind CSS")
    if "playwright" in package_names or (frontend_root / "playwright.config.ts").exists():
        technologies.append("Playwright")
    if "vitest" in package_names or (frontend_root / "vitest.config.ts").exists():
        technologies.append("Vitest")

    deduped: list[str] = []
    seen: set[str] = set()
    for item in technologies:
        key = item.lower()
        if key not in seen:
            deduped.append(item)
            seen.add(key)
    return deduped


def infer_init_hooks(source_root: Path) -> list[dict[str, Any]]:
    scripts_dir = source_root / "scripts"
    init_scripts = sorted(path for path in scripts_dir.glob("*.sh") if "init" in path.name and path.is_file())
    hooks: list[dict[str, Any]] = []
    for script_path in init_scripts:
        relative_path = script_path.relative_to(source_root).as_posix()
        hook_id = re.sub(r"[^a-z0-9]+", "-", script_path.stem.lower()).strip("-")
        hooks.append(
            {
                "id": hook_id or script_path.stem.lower(),
                "kind": "script",
                "path": relative_path,
                "summary": f"Runs {script_path.name} during template-specific initialization.",
            }
        )
    return hooks


def infer_gate_payload(source_root: Path) -> dict[str, str] | None:
    helper_candidates = [
        source_root / "scripts" / "phase-gate.sh",
        source_root / "scripts" / "gate.sh",
    ]
    helper_path = next((path for path in helper_candidates if path.exists()), None)
    stack_docs = source_root / "docs" / "STACK.md"
    if helper_path is None and not stack_docs.exists():
        return None
    payload: dict[str, str] = {}
    if helper_path is not None:
        payload["helper_script"] = helper_path.relative_to(source_root).as_posix()
    if stack_docs.exists():
        payload["stack_docs"] = stack_docs.relative_to(source_root).as_posix()
    return payload or None


def infer_smoke_payload(source_root: Path) -> dict[str, str] | None:
    stack_docs = source_root / "docs" / "STACK.md"
    if not stack_docs.exists():
        return None
    stack_docs_text = stack_docs.read_text(encoding="utf-8").lower()
    anchor = (
        "docs/STACK.md#gate-commands"
        if "gate-commands" in stack_docs_text or "gate commands" in stack_docs_text
        else "docs/STACK.md"
    )
    return {"docs_anchor": anchor}


def choose_template_source_root(template_dir: Path, existing_manifest: dict[str, Any] | None) -> Path:
    if existing_manifest:
        source_root = template_dir / str(existing_manifest.get("source_dir", "source"))
        if source_root.exists():
            return source_root
    if (template_dir / "source").exists():
        return template_dir / "source"
    return template_dir


def build_draft_template_manifest(template_dir: Path, existing_manifest: dict[str, Any] | None) -> dict[str, Any]:
    source_root = choose_template_source_root(template_dir, existing_manifest)
    frontend_root = source_root / "frontend"
    backend_package_manager = detect_backend_package_manager(source_root)
    frontend_package_manager = detect_frontend_package_manager(frontend_root)

    manifest: dict[str, Any] = {
        "manifest_schema_version": str((existing_manifest or {}).get("manifest_schema_version", "0.1")),
        "template_id": str((existing_manifest or {}).get("template_id", template_dir.name)),
        "display_name": str((existing_manifest or {}).get("display_name", slug_to_display_name(template_dir.name))),
        "version": str((existing_manifest or {}).get("version", "0.1.0")),
        "source_dir": os.path.relpath(source_root, template_dir).replace("\\", "/"),
        "technologies": list((existing_manifest or {}).get("technologies", infer_technologies(source_root))),
    }

    package_managers = dict((existing_manifest or {}).get("package_managers", {}))
    if backend_package_manager and "backend" not in package_managers:
        package_managers["backend"] = backend_package_manager
    if frontend_package_manager and "frontend" not in package_managers:
        package_managers["frontend"] = frontend_package_manager
    if package_managers:
        manifest["package_managers"] = package_managers

    init_hooks = list((existing_manifest or {}).get("init_hooks", infer_init_hooks(source_root)))
    if init_hooks:
        manifest["init_hooks"] = init_hooks

    gate_payload = (existing_manifest or {}).get("gate", infer_gate_payload(source_root))
    if gate_payload:
        manifest["gate"] = gate_payload

    smoke_payload = (existing_manifest or {}).get("smoke", infer_smoke_payload(source_root))
    if smoke_payload:
        manifest["smoke"] = smoke_payload

    return manifest


def review_items_for_template_manifest(draft_manifest: dict[str, Any]) -> list[str]:
    items: list[str] = []
    package_managers = draft_manifest.get("package_managers")
    if not isinstance(package_managers, dict) or not package_managers:
        items.append("Confirm package manager fields; no backend/frontend package managers were inferred.")
    if not draft_manifest.get("init_hooks"):
        items.append("Confirm whether the template needs an `init_hooks` entry for stack-specific bootstrap.")
    if not draft_manifest.get("gate"):
        items.append("Confirm gate metadata; no helper script or stack docs were inferred.")
    if not draft_manifest.get("smoke"):
        items.append("Confirm smoke metadata; no stack docs anchor was inferred.")
    if not draft_manifest.get("technologies"):
        items.append("Confirm `technologies`; no recognizable stack markers were inferred.")
    return items


def draft_template_payload(template_dir: Path) -> dict[str, Any]:
    path = template_dir.resolve()
    manifest_path = path / "template.yaml"
    existing_manifest = load_yaml(manifest_path) if manifest_path.exists() else None
    source_root = choose_template_source_root(path, existing_manifest)
    draft_manifest = build_draft_template_manifest(path, existing_manifest)
    gate_payload = draft_manifest.get("gate")
    smoke_payload = draft_manifest.get("smoke")
    package_managers = draft_manifest.get("package_managers", {})
    init_hooks = draft_manifest.get("init_hooks", [])

    payload = {
        "status": "template-registration-draft",
        "template_dir": str(path),
        "template_id": str(draft_manifest["template_id"]),
        "manifest_schema_version": str(draft_manifest["manifest_schema_version"]),
        "display_name": draft_manifest["display_name"],
        "version": draft_manifest["version"],
        "source_dir": draft_manifest["source_dir"],
        "detected": {
            "has_pyproject": (source_root / "pyproject.toml").exists(),
            "has_frontend_package": (source_root / "frontend" / "package.json").exists()
            or (source_root / "package.json").exists(),
            "has_docker_compose": (source_root / "docker-compose.yml").exists(),
            "has_backend_app_dir": (source_root / "app").is_dir(),
            "has_frontend_dir": (source_root / "frontend").is_dir(),
            "has_stack_docs": (source_root / "docs" / "STACK.md").exists(),
            "has_workflow_playbook_compat": (source_root / "docs" / "workflows").is_dir(),
            "backend_package_manager": package_managers.get("backend"),
            "frontend_package_manager": package_managers.get("frontend"),
            "technologies": draft_manifest.get("technologies", []),
            "init_hook_scripts": [hook.get("path") for hook in init_hooks if isinstance(hook, dict)],
            "gate_helper_script": gate_payload.get("helper_script") if isinstance(gate_payload, dict) else None,
            "stack_docs": gate_payload.get("stack_docs") if isinstance(gate_payload, dict) else None,
            "smoke_docs_anchor": smoke_payload.get("docs_anchor") if isinstance(smoke_payload, dict) else None,
        },
        "draft_manifest": draft_manifest,
        "review_items": review_items_for_template_manifest(draft_manifest),
    }

    if existing_manifest is not None:
        payload["manifest"] = existing_manifest
        payload["notes"] = [
            "Template manifest already exists and was loaded from template.yaml.",
            "Review `draft_manifest` against the existing manifest before changing canonical metadata.",
        ]
    else:
        payload["notes"] = [
            "No template.yaml found; this is a draft registration payload.",
            "Use `sdd register-template <path> --write` to write the inferred manifest, then review ambiguous fields.",
        ]
    return payload


def write_template_manifest(template_dir: Path, draft_manifest: dict[str, Any], *, force: bool) -> Path:
    manifest_path = template_dir.resolve() / "template.yaml"
    if manifest_path.exists() and not force:
        raise typer.BadParameter("template.yaml already exists. Re-run with --force to overwrite it.")
    with manifest_path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(draft_manifest, handle, sort_keys=False, allow_unicode=True)
    return manifest_path


def infer_project_slug(target_dir: Path) -> str:
    candidate = slugify_project_name(target_dir.name)
    if candidate:
        return candidate
    raise typer.BadParameter("Could not infer a project slug from the target directory. Pass --project-name.")


def read_origin_project_slug(target_dir: Path) -> str | None:
    origin_path = target_dir / ".sdd-origin.yaml"
    if not origin_path.exists():
        return None
    payload = load_yaml(origin_path)
    project = payload.get("project")
    if isinstance(project, dict):
        slug = project.get("slug")
        if isinstance(slug, str) and slug:
            return slug
    return None


@app.command("init")
def init_command(
    project_name: Annotated[
        str,
        typer.Option("--project-name", help="Project slug used for the generated working copy."),
    ],
    template: Annotated[
        str,
        typer.Option("--template", help="Template id to initialize."),
    ] = "fastapi-nuxt",
    target_dir: Annotated[
        Path | None,
        typer.Argument(help="Optional target directory for the generated working copy."),
    ] = None,
    domain: Annotated[
        str | None,
        typer.Option(
            "--domain",
            help="Optional project domain used for template bootstrap replacements (for example in nginx config).",
        ),
    ] = None,
    admin_email: Annotated[
        str,
        typer.Option("--admin-email", help="Admin email for the compatibility init step."),
    ] = "admin@example.com",
    run_compat_init: Annotated[
        bool,
        typer.Option(
            "--run-compat-init",
            help="Run legacy scripts/init-project.sh after CLI bootstrap (fallback compatibility path).",
        ),
    ] = False,
    apply_template_init: Annotated[
        bool,
        typer.Option(
            "--apply-template-init/--no-apply-template-init",
            help="Apply template placeholder/bootstrap replacements after composing workflow + template.",
        ),
    ] = True,
) -> None:
    project_slug = slugify_project_name(project_name)
    manifest = load_template_manifest(template)
    destination = (target_dir or (Path.cwd() / project_slug)).resolve()
    ensure_empty_target(destination)
    materialize_project(destination, manifest)
    generated_files = write_workflow_project_files(destination, project_slug)
    metadata_files = write_project_metadata(destination, manifest, project_slug)

    typer.echo(f"Initialized {manifest.display_name} from workflow + template at {destination}")
    typer.echo(f"Template manifest: {manifest.manifest_path}")
    typer.echo(f"Canonical playbooks live under {destination / 'workflow' / 'docs' / 'playbooks'}")
    typer.echo(f"Generated managed project files: {', '.join(generated_files)}")
    typer.echo(f"Wrote project metadata: {', '.join(metadata_files)}")

    if apply_template_init:
        bootstrap_payload = apply_template_bootstrap(destination, project_slug, domain, admin_email)
        typer.echo(
            "Applied template bootstrap replacements: "
            f"{bootstrap_payload['changed_count']} files"
            + (" and generated .env" if bootstrap_payload["env_created"] else "")
            + "."
        )
    else:
        typer.echo("Template bootstrap replacements were skipped (--no-apply-template-init).")

    if run_compat_init:
        run_compat_init_script(destination, project_slug, domain, admin_email)
    else:
        typer.echo("Legacy compatibility init script not run.")


@app.command("register-template")
def register_template_command(
    template_path: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Path to inspect and draft-register as a template.",
        ),
    ],
    write: Annotated[
        bool,
        typer.Option(
            "--write/--no-write",
            help="Write the inferred draft manifest to template.yaml.",
        ),
    ] = False,
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            help="Overwrite an existing template.yaml when used with --write.",
        ),
    ] = False,
) -> None:
    payload = draft_template_payload(template_path)
    if write:
        manifest_path = write_template_manifest(template_path, payload["draft_manifest"], force=force)
        payload["written_manifest_path"] = str(manifest_path)
        payload["message"] = (
            "Draft template manifest was written. Review `draft_manifest`, then validate with "
            "`sdd release validate --scope template --template <id> --skip-tag-checks`."
        )
    print_json(payload)


@app.command("integrate")
def integrate_command(
    template: Annotated[
        str,
        typer.Option("--template", help="Template id to use for managed-file and metadata repair."),
    ] = "fastapi-nuxt",
    project_name: Annotated[
        str | None,
        typer.Option(
            "--project-name",
            help="Project slug used when generating missing managed files during integration repair.",
        ),
    ] = None,
    check: Annotated[
        bool,
        typer.Option(
            "--check",
            help="Report what would be repaired without writing files.",
        ),
    ] = False,
    domain: Annotated[
        str | None,
        typer.Option(
            "--domain",
            help="Optional project domain used for template bootstrap replacements.",
        ),
    ] = None,
    admin_email: Annotated[
        str,
        typer.Option("--admin-email", help="Admin email used by template bootstrap replacements."),
    ] = "admin@example.com",
    apply_template_init: Annotated[
        bool,
        typer.Option(
            "--apply-template-init",
            help="Apply template placeholder/bootstrap replacements after repair.",
        ),
    ] = False,
    target_dir: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Project directory to inspect for workflow integration state.",
        ),
    ] = Path("."),
) -> None:
    manifest = load_template_manifest(template)
    target = target_dir.resolve()
    state = detect_repo_shape(target)
    has_agents = state["has_agents_file"]
    has_claude = state["has_claude_file"]
    has_workflow_dir = state["has_workflow_dir"]
    metadata_flags = [
        state["has_origin_metadata"],
        state["has_lock_metadata"],
        state["has_ownership_metadata"],
        state["has_template_manifest_metadata"],
    ]
    has_all_metadata = all(metadata_flags)
    has_any_metadata = any(metadata_flags)

    if (has_agents ^ has_claude) or ((has_agents or has_claude) and not has_workflow_dir):
        print_json(
            {
                "status": "partial-state-detected",
                "project": state,
                "message": (
                    "Partial workflow integration detected. Repair mode is reserved for a later "
                    "slice, so this command will not guess. Restore the missing managed files or "
                    "recreate the project from a clean `sdd init` output."
                ),
            }
        )
        raise typer.Exit(code=1)

    if has_agents and has_claude and has_workflow_dir and has_all_metadata and not apply_template_init:
        print_json(
            {
                "status": "already-integrated",
                "project": state,
                "message": "Managed workflow files and `.sdd-*` metadata are present. No changes applied.",
            }
        )
        return

    can_repair = (
        has_workflow_dir
        and state["has_template_stack_docs"]
        and (state["has_reference_backend"] or state["has_reference_frontend"])
    )
    if can_repair:
        resolved_project_slug = (
            slugify_project_name(project_name)
            if project_name
            else (read_origin_project_slug(target) or infer_project_slug(target))
        )
        planned_actions: list[str] = []
        if not has_agents:
            planned_actions.append("write AGENTS.md")
        if not has_claude:
            planned_actions.append("write CLAUDE.md")
        if not has_all_metadata:
            if has_any_metadata:
                planned_actions.append("repair incomplete .sdd metadata")
            else:
                planned_actions.extend(
                    [
                        "write .sdd-origin.yaml",
                        "write .sdd-lock.yaml",
                        "write .sdd/ownership.yaml",
                        "write .sdd/template-manifest.yaml",
                    ]
                )
        if apply_template_init:
            planned_actions.append("apply template bootstrap replacements")

        if not planned_actions:
            print_json(
                {
                    "status": "already-integrated",
                    "project": state,
                    "message": "No integration repair actions were necessary.",
                }
            )
            return

        if check:
            print_json(
                {
                    "status": "repair-plan",
                    "project": state,
                    "template": manifest.template_id,
                    "project_name": resolved_project_slug,
                    "actions": planned_actions,
                    "message": "Check mode only. No files were written.",
                }
            )
            return

        generated_files: list[str] = []
        metadata_files: list[str] = []
        bootstrap_summary: dict[str, Any] | None = None
        if not (has_agents and has_claude):
            generated_files = write_workflow_project_files(target, resolved_project_slug)
        if not has_all_metadata:
            metadata_files = write_project_metadata(target, manifest, resolved_project_slug)
        if apply_template_init:
            bootstrap_summary = apply_template_bootstrap(target, resolved_project_slug, domain, admin_email)
        if generated_files or metadata_files:
            message = "Missing managed workflow files and metadata were recreated."
            if has_any_metadata and not has_all_metadata:
                message = "Incomplete .sdd metadata was repaired and normalized."
        else:
            message = "Project was already integrated."
        if bootstrap_summary is not None:
            message += " Template bootstrap replacements were applied."
        else:
            message += " Template bootstrap replacements were not requested."

        print_json(
            {
                "status": "repaired-integration",
                "project": detect_repo_shape(target),
                "template": manifest.template_id,
                "project_name": resolved_project_slug,
                "generated_files": generated_files,
                "metadata_files": metadata_files,
                "template_init": bootstrap_summary,
                "message": message,
            }
        )
        return

    if has_workflow_dir and not has_agents and not has_claude and not has_any_metadata:
        print_json(
            {
                "status": "compat-init-required",
                "project": state,
                "message": (
                    "Workflow files and stack files are present, but derived-project instruction "
                    "files have not been generated yet. Run `sdd integrate --apply-template-init` "
                    "to recreate managed files and apply template bootstrap replacements."
                ),
            }
        )
        return

    print_json(
        {
            "status": "not-yet-integrated",
            "project": state,
            "message": (
                "The target does not look like a workflow-composed project yet. Use `sdd init` first "
                "or provide a project that already contains the workflow and template files."
            ),
        }
    )


@app.command("upgrade")
def upgrade_command(
    scope_or_target: Annotated[
        str | None,
        typer.Argument(
            help=(
                "Optional upgrade scope (`all`, `workflow`, `template`) or target project path. "
                "If omitted, the current directory is used."
            )
        ),
    ] = None,
    check: Annotated[
        bool,
        typer.Option(
            "--check/--apply",
            help=(
                "Review the upgrade plan without changing files or apply only safe managed-file "
                "updates against the resolved upgrade source."
            ),
        ),
    ] = True,
    source: Annotated[
        str,
        typer.Option(
            "--source",
            help=(
                "Upgrade target source. Use `released-artifact` for namespaced release tags "
                "or `workspace-current` for maintainer/debugging resolution against the current checkout."
            ),
        ),
    ] = "released-artifact",
    to: Annotated[
        list[str],
        typer.Option(
            "--to",
            help=("Explicit target release, e.g. `--to workflow@v1.2.0` or `--to template@fastapi-nuxt@v0.2.0`."),
        ),
    ] = [],
    target_dir: Annotated[
        Path | None,
        typer.Argument(
            file_okay=False,
            dir_okay=True,
            help="Generated project directory to inspect for upgrade planning.",
        ),
    ] = None,
) -> None:
    candidate = scope_or_target or "all"
    if candidate.lower() in {"all", "workflow", "template"}:
        normalized_scope = candidate.lower()
        resolved_target = (target_dir or Path(".")).resolve()
    else:
        if target_dir is not None:
            raise typer.BadParameter(
                "When the first positional argument is a path, do not pass a second target directory."
            )
        normalized_scope = "all"
        resolved_target = Path(candidate).resolve()

    if normalized_scope not in {"all", "workflow", "template"}:
        raise typer.BadParameter("Upgrade scope must be one of: all, workflow, template.")
    if not resolved_target.exists() or not resolved_target.is_dir():
        raise typer.BadParameter(f"Generated project directory does not exist or is not a directory: {resolved_target}")

    target = resolved_target
    origin_payload, lock_payload, rules = load_upgrade_metadata(target)
    current_manifest = load_template_manifest(str(origin_payload.get("template", {}).get("id", "fastapi-nuxt")))
    project_slug = read_origin_project_slug(target) or infer_project_slug(target)
    resolved_upgrade_target = resolve_upgrade_target(
        source_mode=source,
        scope=normalized_scope,
        requested_targets=to,
        current_manifest=current_manifest,
        origin_payload=origin_payload,
        lock_payload=lock_payload,
    )
    if check:
        print_json(
            build_upgrade_plan(
                project_root=target,
                target=resolved_upgrade_target,
                project_slug=project_slug,
                current_manifest=current_manifest,
                rules=rules,
                lock_payload=lock_payload,
                scope=normalized_scope,
            )
        )
        return

    print_json(
        apply_upgrade(
            project_root=target,
            target=resolved_upgrade_target,
            project_slug=project_slug,
            current_manifest=current_manifest,
            rules=rules,
            lock_payload=lock_payload,
            scope=normalized_scope,
        )
    )


@release_app.command("status")
def release_status_command(
    template: Annotated[
        str,
        typer.Option("--template", help="Template id whose release coordinates should be inspected."),
    ] = "fastapi-nuxt",
) -> None:
    print_json(release_status_payload(template))


@release_app.command("validate")
def release_validate_command(
    template: Annotated[
        str,
        typer.Option("--template", help="Template id whose release inputs should be validated."),
    ] = "fastapi-nuxt",
    scope: Annotated[
        Literal["all", "workflow", "template"],
        typer.Option(
            "--scope",
            help="Validate workflow structure, template structure, or both.",
        ),
    ] = "all",
    workflow_version: Annotated[
        str | None,
        typer.Option(
            "--workflow-version",
            help="Workflow release version to validate, defaulting to `pyproject.toml` `project.version`.",
        ),
    ] = None,
    template_version: Annotated[
        str | None,
        typer.Option(
            "--template-version",
            help="Template release version to validate, defaulting to `template.yaml` `version`.",
        ),
    ] = None,
    expect_existing_tags: Annotated[
        bool,
        typer.Option(
            "--expect-existing-tags/--expect-new-tags",
            help=(
                "Validate against already-published component tags or validate a pre-release state "
                "where the expected tags must not exist yet."
            ),
        ),
    ] = False,
    check_tags: Annotated[
        bool,
        typer.Option(
            "--check-tags/--skip-tag-checks",
            help=(
                "Check release tag existence in addition to validating repository structure. "
                "Use `--skip-tag-checks` for everyday CI and maintainer validation."
            ),
        ),
    ] = True,
) -> None:
    print_json(
        validate_release_payload(
            template=template,
            scope=scope,
            workflow_version=workflow_version,
            template_version=template_version,
            allow_existing_tags=expect_existing_tags,
            check_tags=check_tags,
        )
    )


@gate_app.command("resolve")
def gate_resolve_command(
    project_dir: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Generated project directory whose gate metadata should be resolved.",
        ),
    ] = Path("."),
) -> None:
    target = project_dir.resolve()
    manifest_payload = load_project_template_manifest(target)
    payload = gate_dispatch_payload_from_manifest(target, manifest_payload)
    payload["status"] = "gate-dispatch"
    payload["project"] = str(target)
    payload["manifest_path"] = str(project_template_manifest_path(target))
    print_json(payload)


@dev_app.command("rebuild")
def dev_rebuild_command(
    template: Annotated[
        str,
        typer.Option("--template", help="Template id to materialize under dev/."),
    ] = "fastapi-nuxt",
) -> None:
    manifest = load_template_manifest(template)
    destination = repo_root() / "dev" / template
    if destination.exists():
        shutil.rmtree(destination)
    materialize_project(destination, manifest)
    marker = destination / ".sdd-dev-state.json"
    marker.write_text(
        json.dumps(
            {
                "template": manifest.template_id,
                "template_manifest": str(manifest.manifest_path),
                "canonical_playbooks": str(canonical_playbook_dir()),
                "mode": "workflow-plus-template-generated-dev-workspace",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    typer.echo(f"Rebuilt generated dev workspace at {destination}")


@dev_app.command("diff")
def dev_diff_command(
    template: Annotated[
        str,
        typer.Option("--template", help="Template id whose generated dev workspace should be compared."),
    ] = "fastapi-nuxt",
) -> None:
    manifest = load_template_manifest(template)
    destination = repo_root() / "dev" / template
    if not destination.exists():
        raise typer.BadParameter(f"Generated dev workspace does not exist: {destination}. Run `sdd dev rebuild` first.")
    with tempfile.TemporaryDirectory(prefix="sdd-dev-baseline-") as temp_dir:
        baseline = Path(temp_dir)
        materialize_project(baseline, manifest)
        summary = compare_snapshots(baseline, destination)
    entries = classify_dev_workspace_summary(manifest.template_id, summary)
    authoritative_count = sum(1 for entry in entries if entry["classification"] == "authoritative")
    generated_only_count = len(entries) - authoritative_count
    print_json(
        {
            "status": "dev-diff",
            "template": manifest.template_id,
            "dev_workspace": str(destination),
            "changed_count": len(summary.changed),
            "only_in_baseline_count": len(summary.only_in_repo),
            "only_in_dev_count": len(summary.only_in_dev),
            "authoritative_change_count": authoritative_count,
            "generated_only_change_count": generated_only_count,
            "changed": summary.changed[:50],
            "only_in_baseline": summary.only_in_repo[:50],
            "only_in_dev": summary.only_in_dev[:50],
            "entries": entries[:100],
        }
    )


@dev_app.command("promote")
def dev_promote_command(
    template: Annotated[
        str,
        typer.Option("--template", help="Template id whose dev diff should be classified."),
    ] = "fastapi-nuxt",
) -> None:
    manifest = load_template_manifest(template)
    destination = repo_root() / "dev" / template
    if not destination.exists():
        raise typer.BadParameter(f"Generated dev workspace does not exist: {destination}. Run `sdd dev rebuild` first.")
    with tempfile.TemporaryDirectory(prefix="sdd-dev-baseline-") as temp_dir:
        baseline = Path(temp_dir)
        materialize_project(baseline, manifest)
        summary = compare_snapshots(baseline, destination)
    entries = classify_dev_workspace_summary(manifest.template_id, summary)
    blocked_entries = [entry for entry in entries if entry["classification"] == "generated-only"]
    review_entries = [entry for entry in entries if entry["classification"] == "authoritative"]
    grouped_review_paths: dict[str, list[str]] = {
        "workflow-owned": [entry["path"] for entry in review_entries if entry["owner"] == "workflow"],
        "template-owned": [entry["path"] for entry in review_entries if entry["owner"] == "template"],
    }
    status = "promotion-blocked" if blocked_entries else "promotion-plan"
    message = (
        "Generated-only dev paths were detected. Re-apply only the reviewable entries in canonical "
        "sources; blocked paths must not be promoted."
        if blocked_entries
        else "Review the mapped authoritative targets and re-apply approved changes in canonical sources."
    )
    print_json(
        {
            "status": status,
            "template": manifest.template_id,
            "dev_workspace": str(destination),
            "message": message,
            "reviewable_paths": grouped_review_paths,
            "reviewable_entries": review_entries[:100],
            "blocked_entries": blocked_entries[:100],
        }
    )


def main() -> None:
    app()


if __name__ == "__main__":
    main()
