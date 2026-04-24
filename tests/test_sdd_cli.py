from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from workflow.cli import main as cli_main
from workflow.cli.main import app

runner = CliRunner()


def make_minimal_template_repo(tmp_path: Path, template_id: str = "demo-template") -> Path:
    repo = tmp_path / "repo"
    (repo / "workflow" / "project-files").mkdir(parents=True)
    (repo / "workflow" / "docs" / "playbooks").mkdir(parents=True)
    (repo / "templates" / template_id / "source" / "app").mkdir(parents=True)
    (repo / "templates" / template_id / "source" / "docs").mkdir(parents=True)
    (repo / "workflow" / "__init__.py").write_text("", encoding="utf-8")
    (repo / "workflow" / "project-files" / "AGENTS.md.template").write_text(
        "---\nheader\n---\n# [PROJECT_NAME]\n",
        encoding="utf-8",
    )
    (repo / "workflow" / "project-files" / "CLAUDE.md.template").write_text(
        "---\nheader\n---\n# [PROJECT_NAME]\n",
        encoding="utf-8",
    )
    (repo / "workflow" / "docs" / "playbooks" / "README.md").write_text(
        "# Playbooks\n",
        encoding="utf-8",
    )
    (repo / "templates" / template_id / "template.yaml").write_text(
        "\n".join(
            [
                'manifest_schema_version: "0.1"',
                f'template_id: "{template_id}"',
                'display_name: "Demo Template"',
                'version: "0.1.0"',
                'source_dir: "source"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    (repo / "templates" / template_id / "source" / "app" / "main.py").write_text(
        "print('demo')\n",
        encoding="utf-8",
    )
    (repo / "templates" / template_id / "source" / "docs" / "STACK.md").write_text(
        "# Stack\n",
        encoding="utf-8",
    )
    return repo


def test_register_template_reports_detected_shape(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")
    (source_dir / "frontend").mkdir()
    (source_dir / "frontend" / "package.json").write_text(
        json.dumps(
            {
                "dependencies": {"nuxt": "^4.0.0", "vue": "^3.0.0"},
                "devDependencies": {"typescript": "^5.0.0", "vitest": "^1.0.0"},
            }
        ),
        encoding="utf-8",
    )
    (source_dir / "frontend" / "pnpm-lock.yaml").write_text("lockfileVersion: '9.0'\n", encoding="utf-8")
    (source_dir / "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
    (source_dir / "docs").mkdir()
    (source_dir / "docs" / "STACK.md").write_text("## Gate Commands\n", encoding="utf-8")
    (source_dir / "scripts").mkdir()
    (source_dir / "scripts" / "init-project.sh").write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    (source_dir / "scripts" / "phase-gate.sh").write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    (tmp_path / "template.yaml").write_text(
        "\n".join(
            [
                'manifest_schema_version: "0.1"',
                'template_id: "demo-template"',
                'display_name: "Demo Template"',
                'version: "1.2.3"',
                'source_dir: "source"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["register-template", str(tmp_path)])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["template_id"] == "demo-template"
    assert payload["display_name"] == "Demo Template"
    assert payload["version"] == "1.2.3"
    assert payload["detected"]["has_pyproject"] is True
    assert payload["detected"]["has_frontend_package"] is True
    assert payload["detected"]["has_docker_compose"] is True
    assert payload["manifest"]["source_dir"] == "source"
    assert payload["draft_manifest"]["package_managers"]["frontend"] == "pnpm"
    assert payload["draft_manifest"]["gate"]["helper_script"] == "scripts/phase-gate.sh"
    assert payload["draft_manifest"]["smoke"]["docs_anchor"] == "docs/STACK.md#gate-commands"


def test_register_template_can_write_inferred_manifest(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")
    (source_dir / "uv.lock").write_text("version = 1\n", encoding="utf-8")
    (source_dir / "frontend").mkdir()
    (source_dir / "frontend" / "package.json").write_text(
        json.dumps({"dependencies": {"nuxt": "^4.0.0"}}),
        encoding="utf-8",
    )
    (source_dir / "frontend" / "pnpm-lock.yaml").write_text("lockfileVersion: '9.0'\n", encoding="utf-8")
    (source_dir / "docs").mkdir()
    (source_dir / "docs" / "STACK.md").write_text("## Gate Commands\n", encoding="utf-8")
    (source_dir / "scripts").mkdir()
    (source_dir / "scripts" / "init-project.sh").write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    (source_dir / "scripts" / "phase-gate.sh").write_text("#!/usr/bin/env bash\n", encoding="utf-8")

    result = runner.invoke(app, ["register-template", str(tmp_path), "--write"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    manifest_path = tmp_path / "template.yaml"
    assert manifest_path.exists()
    written_manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    assert payload["written_manifest_path"] == str(manifest_path.resolve())
    assert written_manifest["template_id"] == tmp_path.name
    assert written_manifest["package_managers"]["backend"] == "uv"
    assert written_manifest["package_managers"]["frontend"] == "pnpm"
    assert written_manifest["gate"]["stack_docs"] == "docs/STACK.md"


def test_integrate_flags_partial_state(tmp_path: Path) -> None:
    (tmp_path / "AGENTS.md").write_text("rules\n", encoding="utf-8")

    result = runner.invoke(app, ["integrate", str(tmp_path)])

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["status"] == "partial-state-detected"


def test_init_refuses_non_empty_target(tmp_path: Path) -> None:
    target = tmp_path / "existing-project"
    target.mkdir()
    (target / "README.md").write_text("occupied\n", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "init",
            "--template",
            "fastapi-nuxt",
            "--project-name",
            "demo-project",
            str(target),
        ],
    )

    assert result.exit_code != 0
    assert "Target directory is not empty" in result.stderr


def test_init_composes_project_from_workflow_and_template(tmp_path: Path) -> None:
    target = tmp_path / "generated-project"

    result = runner.invoke(
        app,
        [
            "init",
            "--template",
            "fastapi-nuxt",
            "--project-name",
            "demo-project",
            str(target),
        ],
    )

    assert result.exit_code == 0
    assert (target / "workflow" / "project-files" / "AGENTS.md.template").exists()
    assert (target / "app" / "main.py").exists()
    assert (target / "AGENTS.md").exists()
    assert (target / "CLAUDE.md").exists()
    assert (target / ".sdd-origin.yaml").exists()
    assert (target / ".sdd-lock.yaml").exists()
    assert (target / ".sdd" / "ownership.yaml").exists()
    assert (target / ".sdd" / "template-manifest.yaml").exists()


def test_init_writes_metadata_and_managed_files(tmp_path: Path) -> None:
    target = tmp_path / "generated-project"

    result = runner.invoke(
        app,
        [
            "init",
            "--template",
            "fastapi-nuxt",
            "--project-name",
            "demo-project",
            str(target),
        ],
    )

    assert result.exit_code == 0

    origin_payload = yaml.safe_load((target / ".sdd-origin.yaml").read_text(encoding="utf-8"))
    lock_payload = yaml.safe_load((target / ".sdd-lock.yaml").read_text(encoding="utf-8"))
    ownership_payload = yaml.safe_load((target / ".sdd" / "ownership.yaml").read_text(encoding="utf-8"))
    installed_manifest = yaml.safe_load((target / ".sdd" / "template-manifest.yaml").read_text(encoding="utf-8"))

    assert origin_payload["project"]["slug"] == "demo-project"
    assert origin_payload["template"]["id"] == "fastapi-nuxt"
    assert "workflow/**" in ownership_payload["ownership"]["workflow-managed"]
    assert "scripts/**" in ownership_payload["ownership"]["template-managed"]
    assert "app/**" in ownership_payload["ownership"]["user-owned"]
    assert "pyproject.toml" in ownership_payload["ownership"]["merge-required"]
    assert "AGENTS.md" in lock_payload["workflow"]["baseline_hashes"]
    assert "workflow/cli/main.py" in lock_payload["workflow"]["baseline_hashes"]
    assert "docker-compose.yml" in lock_payload["template"]["baseline_hashes"]
    assert "app/main.py" not in lock_payload["template"]["baseline_hashes"]
    assert installed_manifest["template_id"] == "fastapi-nuxt"
    assert installed_manifest["source_dir"] == "."


@pytest.mark.parametrize("template_id", ["fastapi-nuxt", "fastapi-react-router"])
def test_init_composes_multiple_real_templates(tmp_path: Path, template_id: str) -> None:
    target = tmp_path / template_id

    result = runner.invoke(
        app,
        [
            "init",
            "--template",
            template_id,
            "--project-name",
            "demo-project",
            str(target),
        ],
    )

    assert result.exit_code == 0
    assert (target / "workflow" / "project-files" / "AGENTS.md.template").exists()
    assert (target / "app" / "main.py").exists()
    assert (target / "docs" / "STACK.md").exists()
    assert (target / "AGENTS.md").exists()
    origin_payload = yaml.safe_load((target / ".sdd-origin.yaml").read_text(encoding="utf-8"))
    assert origin_payload["template"]["id"] == template_id


def test_init_react_router_template_copies_frontend_specific_files(tmp_path: Path) -> None:
    target = tmp_path / "react-router-project"

    result = runner.invoke(
        app,
        [
            "init",
            "--template",
            "fastapi-react-router",
            "--project-name",
            "demo-project",
            str(target),
        ],
    )

    assert result.exit_code == 0
    assert (target / "frontend" / "react-router.config.ts").exists()
    assert (target / "frontend" / "app" / "routes" / "home.tsx").exists()
    assert not (target / "frontend" / "nuxt.config.ts").exists()


def test_integrate_reports_compat_init_required(tmp_path: Path) -> None:
    (tmp_path / "workflow").mkdir()
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "STACK.md").write_text("stack\n", encoding="utf-8")
    (tmp_path / "app").mkdir()

    result = runner.invoke(app, ["integrate", str(tmp_path)])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "repaired-integration"
    assert (tmp_path / "AGENTS.md").exists()
    assert (tmp_path / "CLAUDE.md").exists()
    assert (tmp_path / ".sdd-origin.yaml").exists()
    assert (tmp_path / ".sdd-lock.yaml").exists()
    assert (tmp_path / ".sdd" / "ownership.yaml").exists()
    assert (tmp_path / ".sdd" / "template-manifest.yaml").exists()


def test_integrate_check_reports_repair_plan_without_writing(tmp_path: Path) -> None:
    (tmp_path / "workflow").mkdir()
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "STACK.md").write_text("stack\n", encoding="utf-8")
    (tmp_path / "app").mkdir()

    result = runner.invoke(app, ["integrate", "--check", str(tmp_path)])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "repair-plan"
    assert "write AGENTS.md" in payload["actions"]
    assert "write .sdd/template-manifest.yaml" in payload["actions"]
    assert not (tmp_path / "AGENTS.md").exists()
    assert not (tmp_path / ".sdd-origin.yaml").exists()


def test_upgrade_check_reports_review_plan_for_initialized_project(tmp_path: Path) -> None:
    target = tmp_path / "generated-project"

    init_result = runner.invoke(
        app,
        [
            "init",
            "--template",
            "fastapi-nuxt",
            "--project-name",
            "demo-project",
            str(target),
        ],
    )
    assert init_result.exit_code == 0

    result = runner.invoke(app, ["upgrade", "--source", "workspace-current", "--check", str(target)])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "upgrade-plan"
    assert payload["scope"] == "all"
    assert payload["resolution"] == "workspace-current"
    assert payload["summary"]["paths_considered"] > 0
    assert any(entry["path"] == "AGENTS.md" for entry in payload["entries"])


def test_upgrade_check_reports_review_plan_for_react_router_template(tmp_path: Path) -> None:
    target = tmp_path / "generated-project"

    init_result = runner.invoke(
        app,
        [
            "init",
            "--template",
            "fastapi-react-router",
            "--project-name",
            "demo-project",
            str(target),
        ],
    )
    assert init_result.exit_code == 0

    result = runner.invoke(app, ["upgrade", "--source", "workspace-current", "--check", str(target)])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "upgrade-plan"
    assert payload["resolution"] == "workspace-current"
    assert payload["template"] == "fastapi-react-router"


def test_gate_resolve_uses_installed_template_manifest(tmp_path: Path) -> None:
    target = tmp_path / "generated-project"

    init_result = runner.invoke(
        app,
        [
            "init",
            "--template",
            "fastapi-nuxt",
            "--project-name",
            "demo-project",
            str(target),
        ],
    )
    assert init_result.exit_code == 0

    result = runner.invoke(app, ["gate", "resolve", str(target)])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "gate-dispatch"
    assert payload["template"]["id"] == "fastapi-nuxt"
    assert payload["gate"]["helper_script"] == "scripts/phase-gate.sh"
    assert payload["gate"]["helper_script_exists"] is True
    assert payload["gate"]["stack_docs"] == "docs/STACK.md"
    assert payload["gate"]["stack_docs_exists"] is True
    assert payload["gate"]["smoke_docs_anchor"] == "docs/STACK.md#gate-commands"


def test_gate_resolve_supports_react_router_template(tmp_path: Path) -> None:
    target = tmp_path / "generated-project"

    init_result = runner.invoke(
        app,
        [
            "init",
            "--template",
            "fastapi-react-router",
            "--project-name",
            "demo-project",
            str(target),
        ],
    )
    assert init_result.exit_code == 0

    result = runner.invoke(app, ["gate", "resolve", str(target)])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "gate-dispatch"
    assert payload["template"]["id"] == "fastapi-react-router"
    assert payload["gate"]["helper_script"] == "scripts/phase-gate.sh"
    assert payload["gate"]["stack_docs"] == "docs/STACK.md"
    assert payload["gate"]["smoke_docs_anchor"] == "docs/STACK.md#gate-commands"


def test_register_template_reports_actual_react_router_template_shape() -> None:
    template_dir = cli_main.repo_root() / "templates" / "fastapi-react-router"

    result = runner.invoke(app, ["register-template", str(template_dir)])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["template_id"] == "fastapi-react-router"
    assert payload["manifest"]["package_managers"]["frontend"] == "pnpm"
    assert "React Router 7" in payload["draft_manifest"]["technologies"]
    assert payload["draft_manifest"]["gate"]["helper_script"] == "scripts/phase-gate.sh"


def test_dev_diff_marks_generated_only_paths_separately(tmp_path: Path, monkeypatch) -> None:
    repo = make_minimal_template_repo(tmp_path)
    monkeypatch.setattr(cli_main, "repo_root", lambda: repo)

    rebuild_result = runner.invoke(app, ["dev", "rebuild", "--template", "demo-template"])
    assert rebuild_result.exit_code == 0

    dev_workspace = repo / "dev" / "demo-template"
    (dev_workspace / "AGENTS.md").write_text("# Rendered file\n", encoding="utf-8")
    (dev_workspace / "app" / "main.py").write_text("print('changed')\n", encoding="utf-8")

    result = runner.invoke(app, ["dev", "diff", "--template", "demo-template"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "dev-diff"
    assert payload["authoritative_change_count"] == 1
    assert payload["generated_only_change_count"] == 1
    generated_entry = next(entry for entry in payload["entries"] if entry["path"] == "AGENTS.md")
    assert generated_entry["classification"] == "generated-only"
    assert generated_entry["status"] == "blocked"
    authoritative_entry = next(entry for entry in payload["entries"] if entry["path"] == "app/main.py")
    assert authoritative_entry["classification"] == "authoritative"
    assert authoritative_entry["owner"] == "template"


def test_dev_promote_blocks_generated_only_paths_and_maps_authoritative_targets(tmp_path: Path, monkeypatch) -> None:
    repo = make_minimal_template_repo(tmp_path)
    monkeypatch.setattr(cli_main, "repo_root", lambda: repo)

    rebuild_result = runner.invoke(app, ["dev", "rebuild", "--template", "demo-template"])
    assert rebuild_result.exit_code == 0

    dev_workspace = repo / "dev" / "demo-template"
    (dev_workspace / "AGENTS.md").write_text("# Rendered file\n", encoding="utf-8")
    workflow_file = dev_workspace / "workflow" / "docs" / "playbooks" / "README.md"
    workflow_file.write_text("# Changed Playbooks\n", encoding="utf-8")

    result = runner.invoke(app, ["dev", "promote", "--template", "demo-template"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "promotion-blocked"
    blocked_entry = next(entry for entry in payload["blocked_entries"] if entry["path"] == "AGENTS.md")
    assert blocked_entry["suggested_authoritative_target"].endswith("workflow/project-files/AGENTS.md.template")
    review_entry = next(
        entry for entry in payload["reviewable_entries"] if entry["path"] == "workflow/docs/playbooks/README.md"
    )
    assert review_entry["owner"] == "workflow"
    assert review_entry["suggested_authoritative_target"].endswith("workflow/docs/playbooks/README.md")


def test_upgrade_workflow_check_keeps_local_changes_when_target_matches_baseline(
    tmp_path: Path,
) -> None:
    target = tmp_path / "generated-project"

    init_result = runner.invoke(
        app,
        [
            "init",
            "--template",
            "fastapi-nuxt",
            "--project-name",
            "demo-project",
            str(target),
        ],
    )
    assert init_result.exit_code == 0

    agents_path = target / "AGENTS.md"
    agents_path.write_text(agents_path.read_text(encoding="utf-8") + "\nLocal note.\n", encoding="utf-8")

    result = runner.invoke(app, ["upgrade", "workflow", "--source", "workspace-current", "--check", str(target)])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    agents_entry = next(entry for entry in payload["entries"] if entry["path"] == "AGENTS.md")
    assert agents_entry["ownership"] == "workflow-managed"
    assert agents_entry["action"] == "keep-local"


def test_upgrade_workflow_apply_updates_managed_file_and_lock_metadata(tmp_path: Path, monkeypatch) -> None:
    target = tmp_path / "generated-project"

    init_result = runner.invoke(
        app,
        [
            "init",
            "--template",
            "fastapi-nuxt",
            "--project-name",
            "demo-project",
            str(target),
        ],
    )
    assert init_result.exit_code == 0

    original = cli_main.build_upgrade_target_snapshot

    def patched_target_snapshot(target_spec, project_slug):
        temp_dir, snapshot = original(target_spec, project_slug)
        agents_path = snapshot / "AGENTS.md"
        agents_path.write_text(
            agents_path.read_text(encoding="utf-8") + "\nUpstream workflow note.\n",
            encoding="utf-8",
        )
        return temp_dir, snapshot

    monkeypatch.setattr(cli_main, "build_upgrade_target_snapshot", patched_target_snapshot)

    result = runner.invoke(app, ["upgrade", "workflow", "--source", "workspace-current", "--apply", str(target)])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "upgrade-applied"
    assert "AGENTS.md" in payload["applied"]["paths"]
    updated_agents = (target / "AGENTS.md").read_text(encoding="utf-8")
    assert "Upstream workflow note." in updated_agents

    lock_payload = yaml.safe_load((target / ".sdd-lock.yaml").read_text(encoding="utf-8"))
    expected_hash = hashlib.sha256(updated_agents.encode("utf-8")).hexdigest()
    assert lock_payload["workflow"]["baseline_hashes"]["AGENTS.md"] == expected_hash


def test_upgrade_workflow_apply_reports_partial_when_merge_required(tmp_path: Path, monkeypatch) -> None:
    target = tmp_path / "generated-project"

    init_result = runner.invoke(
        app,
        [
            "init",
            "--template",
            "fastapi-nuxt",
            "--project-name",
            "demo-project",
            str(target),
        ],
    )
    assert init_result.exit_code == 0

    agents_path = target / "AGENTS.md"
    local_lines = agents_path.read_text(encoding="utf-8").splitlines()
    local_lines[0] = "# Local override"
    agents_path.write_text("\n".join(local_lines) + "\n", encoding="utf-8")

    original = cli_main.build_upgrade_target_snapshot

    def patched_target_snapshot(target_spec, project_slug):
        temp_dir, snapshot = original(target_spec, project_slug)
        upstream_agents = snapshot / "AGENTS.md"
        upstream_lines = upstream_agents.read_text(encoding="utf-8").splitlines()
        upstream_lines[0] = "# Upstream override"
        upstream_agents.write_text("\n".join(upstream_lines) + "\n", encoding="utf-8")
        return temp_dir, snapshot

    monkeypatch.setattr(cli_main, "build_upgrade_target_snapshot", patched_target_snapshot)

    result = runner.invoke(app, ["upgrade", "workflow", "--source", "workspace-current", "--apply", str(target)])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "upgrade-partial"
    assert "AGENTS.md" in payload["blocked"]
    updated_agents = (target / "AGENTS.md").read_text(encoding="utf-8")
    assert "# Local override" in updated_agents
    assert "# Upstream override" not in updated_agents


def test_upgrade_workflow_check_reports_auto_merge_for_clean_text_merge(tmp_path: Path, monkeypatch) -> None:
    target = tmp_path / "generated-project"

    init_result = runner.invoke(
        app,
        [
            "init",
            "--template",
            "fastapi-nuxt",
            "--project-name",
            "demo-project",
            str(target),
        ],
    )
    assert init_result.exit_code == 0

    agents_path = target / "AGENTS.md"
    local_lines = agents_path.read_text(encoding="utf-8").splitlines()
    local_lines[0] = "# Local project note"
    agents_path.write_text("\n".join(local_lines) + "\n", encoding="utf-8")

    original = cli_main.build_upgrade_target_snapshot

    def patched_target_snapshot(target_spec, project_slug):
        temp_dir, snapshot = original(target_spec, project_slug)
        upstream_agents = snapshot / "AGENTS.md"
        upstream_agents.write_text(
            upstream_agents.read_text(encoding="utf-8") + "\nUpstream workflow note.\n",
            encoding="utf-8",
        )
        return temp_dir, snapshot

    monkeypatch.setattr(cli_main, "build_upgrade_target_snapshot", patched_target_snapshot)

    result = runner.invoke(app, ["upgrade", "workflow", "--source", "workspace-current", "--check", str(target)])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    agents_entry = next(entry for entry in payload["entries"] if entry["path"] == "AGENTS.md")
    assert agents_entry["action"] == "auto-merge"
    assert payload["summary"]["auto_merge"] == 1


def test_upgrade_workflow_apply_writes_clean_merged_result(tmp_path: Path, monkeypatch) -> None:
    target = tmp_path / "generated-project"

    init_result = runner.invoke(
        app,
        [
            "init",
            "--template",
            "fastapi-nuxt",
            "--project-name",
            "demo-project",
            str(target),
        ],
    )
    assert init_result.exit_code == 0

    agents_path = target / "AGENTS.md"
    local_lines = agents_path.read_text(encoding="utf-8").splitlines()
    local_lines[0] = "# Local project note"
    agents_path.write_text("\n".join(local_lines) + "\n", encoding="utf-8")

    original = cli_main.build_upgrade_target_snapshot

    def patched_target_snapshot(target_spec, project_slug):
        temp_dir, snapshot = original(target_spec, project_slug)
        upstream_agents = snapshot / "AGENTS.md"
        upstream_agents.write_text(
            upstream_agents.read_text(encoding="utf-8") + "\nUpstream workflow note.\n",
            encoding="utf-8",
        )
        return temp_dir, snapshot

    monkeypatch.setattr(cli_main, "build_upgrade_target_snapshot", patched_target_snapshot)

    result = runner.invoke(app, ["upgrade", "workflow", "--source", "workspace-current", "--apply", str(target)])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "upgrade-applied"
    assert payload["applied"]["auto_merge"] == 1
    merged_agents = (target / "AGENTS.md").read_text(encoding="utf-8")
    assert "# Local project note" in merged_agents
    assert "Upstream workflow note." in merged_agents


def test_upgrade_check_defaults_to_released_artifact_resolution(tmp_path: Path, monkeypatch) -> None:
    target = tmp_path / "generated-project"

    init_result = runner.invoke(
        app,
        [
            "init",
            "--template",
            "fastapi-nuxt",
            "--project-name",
            "demo-project",
            str(target),
        ],
    )
    assert init_result.exit_code == 0

    monkeypatch.setattr(
        cli_main,
        "release_tags_for_prefix",
        lambda prefix: (["workflow/v0.2.0"] if prefix == "workflow/" else ["template/fastapi-nuxt/v0.2.0"]),
    )

    def fake_release_manifest(template_id: str, template_tag: str):
        manifest = cli_main.load_template_manifest(template_id)
        manifest.version = template_tag.removeprefix(f"template/{template_id}/")
        return manifest

    monkeypatch.setattr(cli_main, "load_release_template_manifest", fake_release_manifest)

    def fake_extract(tag: str, repo_path: str, destination: Path) -> None:
        if repo_path == "workflow":
            source = cli_main.repo_root() / "workflow"
            (destination / "workflow").parent.mkdir(parents=True, exist_ok=True)
            cli_main.shutil.copytree(source, destination / "workflow")
            return
        if repo_path == "templates/fastapi-nuxt/source":
            source = cli_main.repo_root() / "templates" / "fastapi-nuxt" / "source"
            target_root = destination / "templates" / "fastapi-nuxt" / "source"
            target_root.parent.mkdir(parents=True, exist_ok=True)
            cli_main.shutil.copytree(source, target_root)
            return
        raise AssertionError(f"Unexpected repo path: {repo_path}")

    monkeypatch.setattr(cli_main, "extract_git_tree", fake_extract)

    result = runner.invoke(app, ["upgrade", "--check", str(target)])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["resolution"] == "released-artifact"
    assert payload["target"]["workflow"] == "v0.2.0"
    assert payload["target"]["template"] == "v0.2.0"


def test_upgrade_apply_uses_released_artifact_source(tmp_path: Path, monkeypatch) -> None:
    target = tmp_path / "generated-project"

    init_result = runner.invoke(
        app,
        [
            "init",
            "--template",
            "fastapi-nuxt",
            "--project-name",
            "demo-project",
            str(target),
        ],
    )
    assert init_result.exit_code == 0

    monkeypatch.setattr(
        cli_main,
        "release_tags_for_prefix",
        lambda prefix: (["workflow/v0.2.0"] if prefix == "workflow/" else ["template/fastapi-nuxt/v0.2.0"]),
    )

    def fake_release_manifest(template_id: str, template_tag: str):
        manifest = cli_main.load_template_manifest(template_id)
        manifest.version = template_tag.removeprefix(f"template/{template_id}/")
        return manifest

    monkeypatch.setattr(cli_main, "load_release_template_manifest", fake_release_manifest)

    def fake_extract(tag: str, repo_path: str, destination: Path) -> None:
        if repo_path == "workflow":
            source = cli_main.repo_root() / "workflow"
            target_root = destination / "workflow"
            target_root.parent.mkdir(parents=True, exist_ok=True)
            cli_main.shutil.copytree(source, target_root)
            return
        if repo_path == "templates/fastapi-nuxt/source":
            source = cli_main.repo_root() / "templates" / "fastapi-nuxt" / "source"
            target_root = destination / "templates" / "fastapi-nuxt" / "source"
            target_root.parent.mkdir(parents=True, exist_ok=True)
            cli_main.shutil.copytree(source, target_root)
            agents_path = target_root / "scripts" / "init-project.sh"
            agents_path.write_text(
                agents_path.read_text(encoding="utf-8") + "\n# released artifact change\n",
                encoding="utf-8",
            )
            return
        raise AssertionError(f"Unexpected repo path: {repo_path}")

    monkeypatch.setattr(cli_main, "extract_git_tree", fake_extract)

    result = runner.invoke(app, ["upgrade", "template", "--apply", str(target)])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "upgrade-applied"
    assert payload["resolution"] == "released-artifact"
    assert "scripts/init-project.sh" in payload["applied"]["paths"]
    script_content = (target / "scripts" / "init-project.sh").read_text(encoding="utf-8")
    assert "# released artifact change" in script_content

    lock_payload = yaml.safe_load((target / ".sdd-lock.yaml").read_text(encoding="utf-8"))
    assert lock_payload["template"]["version"] == "v0.2.0"
    assert "pending_version" not in lock_payload["template"]


def test_upgrade_check_fails_without_release_artifacts(tmp_path: Path) -> None:
    target = tmp_path / "generated-project"

    init_result = runner.invoke(
        app,
        [
            "init",
            "--template",
            "fastapi-nuxt",
            "--project-name",
            "demo-project",
            str(target),
        ],
    )
    assert init_result.exit_code == 0

    result = runner.invoke(app, ["upgrade", "--check", str(target)])

    assert result.exit_code != 0
    assert "No released artifacts found" in result.stderr


def test_upgrade_workspace_current_rejects_explicit_release_targets(tmp_path: Path) -> None:
    target = tmp_path / "generated-project"

    init_result = runner.invoke(
        app,
        [
            "init",
            "--template",
            "fastapi-nuxt",
            "--project-name",
            "demo-project",
            str(target),
        ],
    )
    assert init_result.exit_code == 0

    result = runner.invoke(
        app,
        [
            "upgrade",
            "--source",
            "workspace-current",
            "--to",
            "workflow@v0.2.0",
            "--check",
            str(target),
        ],
    )

    assert result.exit_code != 0
    assert "`--to` targets require `--source released-artifact`" in result.stderr


def test_release_status_reports_expected_and_latest_component_tags(monkeypatch) -> None:
    monkeypatch.setattr(cli_main, "repo_is_dirty", lambda: False)
    monkeypatch.setattr(
        cli_main,
        "release_tags_for_prefix",
        lambda prefix: (
            ["workflow/v0.0.9", "workflow/v0.1.0"]
            if prefix == "workflow/"
            else ["template/fastapi-nuxt/v0.0.9", "template/fastapi-nuxt/v0.1.0"]
        ),
    )

    result = runner.invoke(app, ["release", "status", "--template", "fastapi-nuxt"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "release-status"
    assert payload["workflow"]["expected_tag"] == "workflow/v0.1.0"
    assert payload["workflow"]["expected_tag_exists"] is True
    assert payload["workflow"]["latest_version"] == "v0.1.0"
    assert payload["template"]["expected_tag"] == "template/fastapi-nuxt/v0.1.0"
    assert payload["template"]["expected_tag_exists"] is True
    assert payload["template"]["latest_version"] == "v0.1.0"


def test_release_validate_passes_for_prerelease_state_with_new_tags(monkeypatch) -> None:
    monkeypatch.setattr(cli_main, "release_tags_for_prefix", lambda prefix: [])

    result = runner.invoke(app, ["release", "validate", "--template", "fastapi-nuxt"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "release-validation"
    assert payload["ok"] is True
    assert payload["scope"] == "all"
    assert payload["workflow"]["tag"] == "workflow/v0.1.0"
    assert payload["template_release"]["tag"] == "template/fastapi-nuxt/v0.1.0"
    assert payload["tag_policy"] == "new"


def test_release_validate_passes_for_react_router_template_with_tag_checks_skipped(
    monkeypatch,
) -> None:
    monkeypatch.setattr(cli_main, "release_tags_for_prefix", lambda prefix: [])

    result = runner.invoke(
        app,
        [
            "release",
            "validate",
            "--scope",
            "template",
            "--template",
            "fastapi-react-router",
            "--skip-tag-checks",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["scope"] == "template"
    assert payload["template_release"]["tag"] == "template/fastapi-react-router/v0.1.0"


def test_release_validate_can_ignore_tag_state_for_structural_checks(monkeypatch) -> None:
    monkeypatch.setattr(
        cli_main,
        "release_tags_for_prefix",
        lambda prefix: (["workflow/v0.1.0"] if prefix == "workflow/" else ["template/fastapi-nuxt/v0.1.0"]),
    )

    result = runner.invoke(
        app,
        ["release", "validate", "--template", "fastapi-nuxt", "--skip-tag-checks"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["scope"] == "all"
    assert payload["tag_policy"] == "ignore"
    assert "Release tag existence checks were skipped" in payload["warnings"][0]


def test_release_validate_scope_template_skips_workflow_tag_requirement(monkeypatch) -> None:
    monkeypatch.setattr(
        cli_main,
        "release_tags_for_prefix",
        lambda prefix: [] if prefix == "workflow/" else ["template/fastapi-nuxt/v0.1.0"],
    )

    result = runner.invoke(
        app,
        [
            "release",
            "validate",
            "--scope",
            "template",
            "--template",
            "fastapi-nuxt",
            "--expect-existing-tags",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["scope"] == "template"
    assert payload["tag_policy"] == "existing"


def test_release_validate_fails_when_expected_existing_tags_are_missing(monkeypatch) -> None:
    monkeypatch.setattr(cli_main, "release_tags_for_prefix", lambda prefix: [])

    result = runner.invoke(
        app,
        ["release", "validate", "--template", "fastapi-nuxt", "--expect-existing-tags"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["tag_policy"] == "existing"
    assert "Expected workflow release tag does not exist: workflow/v0.1.0" in payload["errors"]
    assert "Expected template release tag does not exist: template/fastapi-nuxt/v0.1.0" in payload["errors"]
