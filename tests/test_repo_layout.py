from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

LEGACY_ROOT_PATHS = [
    ".claude",
    "app",
    "frontend",
    "alembic",
    "nginx",
    "plugins",
    "scripts",
    "Dockerfile.backend",
    "Dockerfile.frontend",
    "Makefile",
    "alembic.ini",
    "entrypoint.sh",
    "docker-compose.yml",
    "docker-compose.override.yml",
    "docker-compose.prod.yml",
    "docker-compose.ci.yml",
    ".env.example",
    "DEPLOY.md",
    "TODO.md",
    "docs/AGENT_SETUP.md",
    "docs/CHANGELOG.md",
    "docs/CONTEXT.md",
    "docs/DECISIONS.md",
    "docs/E2E_PIPELINE_CHECKLIST.md",
    "docs/KNOWN_GOTCHAS.md",
    "docs/PHASE_01.md",
    "docs/PHASE_TEMPLATE.md",
    "docs/SPEC.md",
    "docs/STACK.md",
    "docs/STATE.md",
    "docs/workflows",
    ".github/workflows/deploy.yml",
]


def test_root_repository_no_longer_contains_legacy_stack_snapshot() -> None:
    for relative_path in LEGACY_ROOT_PATHS:
        assert not (
            REPO_ROOT / relative_path
        ).exists(), f"Legacy root stack path should not exist anymore: {relative_path}"


DOC_FILES = [
    "AGENTS.md",
    "CLAUDE.md",
    "README.md",
    "docs/TEMPLATE_AUTHORING.md",
    "workflow/docs/playbooks/README.md",
    "workflow/docs/playbooks/spec-init.md",
    "workflow/docs/playbooks/phase-init.md",
    "workflow/docs/playbooks/phase-gate.md",
]

FORBIDDEN_DOC_REFERENCES = [
    "human-instructions/",
    "docs/workflows/",
]


def test_repo_maintainer_docs_do_not_reference_removed_layout() -> None:
    for relative_path in DOC_FILES:
        content = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        for forbidden in FORBIDDEN_DOC_REFERENCES:
            assert forbidden not in content, f"{relative_path} should not reference removed path {forbidden}"


def test_repo_maintainer_skill_exists() -> None:
    skill_path = REPO_ROOT / ".codex" / "skills" / "template-repo-maintainer" / "SKILL.md"
    assert skill_path.exists(), "Repo maintainer skill should exist"
    content = skill_path.read_text(encoding="utf-8")
    assert "template-repo-maintainer" in content
    assert "Do not run:" in content
