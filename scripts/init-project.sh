#!/usr/bin/env bash
# init-project.sh — initialise a new project cloned from sdd-template.
# Replaces all placeholders in source files and creates .env.
#
# Usage:
#   ./scripts/init-project.sh <project-slug> <domain> [admin-email]
#
# Arguments:
#   project-slug   kebab-case identifier, e.g. user-dashboard
#   domain         production domain without protocol, e.g. example.com
#   admin-email    optional; default: admin@example.com
#
# Example:
#   ./scripts/init-project.sh user-dashboard example.com admin@example.com

set -euo pipefail

# ── helpers ──────────────────────────────────────────────────────────────────

usage() {
  sed -n '2,14p' "$0" | sed 's/^# \{0,1\}//'
  exit 0
}

die() { echo "Error: $*" >&2; exit 1; }

# Cross-platform in-place sed (GNU/Linux and BSD/macOS).
sedi() {
  if [[ "$(uname)" == "Darwin" ]]; then
    sed -i '' "$@"
  else
    sed -i "$@"
  fi
}

# "my-awesome-app" → "My Awesome App"
to_display_name() {
  echo "$1" | tr '-' ' ' | awk '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) substr($i,2)} 1'
}

# "my-awesome-app" → "my_awesome_app"
to_db_name() {
  echo "$1" | tr '-' '_'
}

# ── argument handling ─────────────────────────────────────────────────────────

[[ "${1:-}" =~ ^(-h|--help)$ ]] && usage
[[ $# -lt 2 ]] && { echo "Error: at least 2 arguments required."; echo; usage; }

PROJECT_SLUG="$1"
DOMAIN="${2#http://}"
DOMAIN="${DOMAIN#https://}"
DOMAIN="${DOMAIN%/}"
ADMIN_EMAIL="${3:-admin@example.com}"

[[ "$PROJECT_SLUG" =~ ^[a-z][a-z0-9-]+$ ]] \
  || die "project-slug must be lowercase kebab-case (e.g. my-app). Got: '$PROJECT_SLUG'"

[[ "$DOMAIN" =~ ^[a-zA-Z0-9]([a-zA-Z0-9.-]*[a-zA-Z0-9])?$ ]] \
  || die "domain must be a bare hostname without protocol (e.g. example.com). Got: '$DOMAIN'"

# ── derived values ────────────────────────────────────────────────────────────

PROJECT_DISPLAY=$(to_display_name "$PROJECT_SLUG")
DB_NAME=$(to_db_name "$PROJECT_SLUG")

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$ROOT_DIR"

# ── idempotency guard ─────────────────────────────────────────────────────────

if ! grep -q '\[PROJECT_NAME\]' docs/SPEC.md 2>/dev/null; then
  echo "Warning: [PROJECT_NAME] not found in docs/SPEC.md."
  echo "This script may have already been run. Re-running will overwrite .env."
  echo ""
  read -r -p "Continue anyway? [y/N] " confirm
  [[ "$confirm" =~ ^[Yy]$ ]] || exit 0
fi

# ── generate secrets ──────────────────────────────────────────────────────────

command -v python3 &>/dev/null || die "python3 is required to generate secrets."

SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
DB_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(24))")

# ── banner ────────────────────────────────────────────────────────────────────

echo ""
echo "Initialising project: $PROJECT_DISPLAY"
echo "  Slug:   $PROJECT_SLUG"
echo "  DB:     $DB_NAME"
echo "  Domain: $DOMAIN"
echo "  Admin:  $ADMIN_EMAIL"
echo ""

# ── create .env ───────────────────────────────────────────────────────────────

# Pin the derived project's DB name into .env.example so it stays consistent
# for anything downstream (setup-prod.sh on the VPS reads POSTGRES_DB from here).
sedi "s|myapp|$DB_NAME|g" .env.example

cp .env.example .env

# DB name — both POSTGRES_DB and DATABASE_URL already replaced in .env.example,
# so this runs on any stragglers introduced later in this script.
sedi "s|myapp|$DB_NAME|g" .env
# Line-anchored replacements on the KEY (stable across .env.example edits).
sedi "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$DB_PASSWORD|" .env
sedi "s|^DATABASE_URL=.*|DATABASE_URL=postgresql+asyncpg://app_user:$DB_PASSWORD@db:5432/$DB_NAME|" .env
sedi "s|^SECRET_KEY=.*|SECRET_KEY=$SECRET_KEY|" .env
# Domain placeholders (commented production lines).
sedi "s|\[DOMAIN\]|$DOMAIN|g" .env
# Project name comment header.
sedi "s|# \[PROJECT_NAME\]|# $PROJECT_DISPLAY|g" .env

echo "  ✓ .env created"

# ── README.md ─────────────────────────────────────────────────────────────────

sedi "s|\[PROJECT_NAME\]|$PROJECT_DISPLAY|g" README.md
echo "  ✓ README.md"

# ── pyproject.toml ────────────────────────────────────────────────────────────

sedi "s|name = \"my-project\"|name = \"$PROJECT_SLUG\"|g" pyproject.toml
sedi "s|\[PROJECT_NAME\] backend|$PROJECT_DISPLAY backend|g" pyproject.toml
echo "  ✓ pyproject.toml"

# ── regenerate uv.lock ────────────────────────────────────────────────────────
# pyproject.toml was renamed; uv.lock must be updated or `uv sync --frozen`
# (used inside Dockerfile.backend) will fail with "Missing workspace member".

if command -v uv &>/dev/null; then
  uv lock --quiet
  echo "  ✓ uv.lock (regenerated)"
else
  echo "  ⚠ uv not found — run 'uv lock' before docker compose up --build"
fi

# ── app/main.py ───────────────────────────────────────────────────────────────

sedi 's|title="\[PROJECT_NAME\]"|title="'"$PROJECT_DISPLAY"'"|' app/main.py
sedi 's|description="\[PROJECT_DESCRIPTION\]"|description="'"$PROJECT_DISPLAY"' backend"|' app/main.py
echo "  ✓ app/main.py"

# ── frontend ──────────────────────────────────────────────────────────────────

# Replace [PROJECT_NAME] in any Vue template under the frontend app (covers
# pages, layouts, widgets — so new components added to the template don't
# silently leak the placeholder).
while IFS= read -r -d '' file; do
  sedi "s|\[PROJECT_NAME\]|$PROJECT_DISPLAY|g" "$file"
done < <(find frontend/app -type f -name '*.vue' -print0)
echo "  ✓ frontend/"

# ── nginx/nginx.conf ──────────────────────────────────────────────────────────

sedi "s|\[DOMAIN\]|$DOMAIN|g" nginx/nginx.conf
echo "  ✓ nginx/nginx.conf"

# ── docker-compose.yml ────────────────────────────────────────────────────────
# Replace the myapp fallback so `docker compose config` doesn't surface it.

sedi "s|:-myapp}|:-$DB_NAME}|g" docker-compose.yml
echo "  ✓ docker-compose.yml"

# ── dev-default DB name in backend ───────────────────────────────────────────
# app/core/config.py and alembic/env.py ship a localhost fallback URL containing
# "myapp". These fallbacks only fire when DATABASE_URL is unset, but replace
# them so new projects don't carry the template's name.

sedi "s|localhost:5432/myapp|localhost:5432/$DB_NAME|g" app/core/config.py
sedi "s|localhost:5432/myapp|localhost:5432/$DB_NAME|g" alembic/env.py
echo "  ✓ app/core/config.py, alembic/env.py"

# ── DEPLOY.md example DB name ─────────────────────────────────────────────────
# DEPLOY.md uses "myapp" in example pg_dump / psql commands. Replace to match
# the derived project's actual DB name.

sedi "s|myapp|$DB_NAME|g" DEPLOY.md
echo "  ✓ DEPLOY.md"

# ── .github/workflows/ci.yml ─────────────────────────────────────────────────

sedi "s|my-project-backend:ci|$PROJECT_SLUG-backend:ci|g" .github/workflows/ci.yml
sedi "s|my-project-frontend:ci|$PROJECT_SLUG-frontend:ci|g" .github/workflows/ci.yml
# myapp → db_name (covers both myapp_test and myapp inside DATABASE_URL)
sedi "s|myapp|$DB_NAME|g" .github/workflows/ci.yml
echo "  ✓ .github/workflows/ci.yml"

# ── docs/ ─────────────────────────────────────────────────────────────────────

sedi "s|\[PROJECT_NAME\]|$PROJECT_DISPLAY|g" docs/SPEC.md
sedi "s|\[PROJECT_NAME\]|$PROJECT_DISPLAY|g" docs/STATE.md
sedi "s|myapp|$DB_NAME|g" docs/PHASE_01.md
sedi "s|myapp|$DB_NAME|g" docs/PHASE_TEMPLATE.md
echo "  ✓ docs/"

# ── AGENTS.md ─────────────────────────────────────────────────────────────────

tail -n +7 human-instructions/AGENTS.for-new-projects.md > AGENTS.md
sedi "s|\[PROJECT_NAME\]|$PROJECT_DISPLAY|g" AGENTS.md
echo "  ✓ AGENTS.md"

# ── CLAUDE.md ─────────────────────────────────────────────────────────────────
# Strip the 6-line template header from human-instructions/CLAUDE.for-new-projects.md,
# then replace [PROJECT_NAME] in the result.

tail -n +7 human-instructions/CLAUDE.for-new-projects.md > CLAUDE.md
sedi "s|\[PROJECT_NAME\]|$PROJECT_DISPLAY|g" CLAUDE.md
echo "  ✓ CLAUDE.md"

# ── alembic migration (admin email) ──────────────────────────────────────────

if [[ "$ADMIN_EMAIL" != "admin@example.com" ]]; then
  sedi "s|admin@example\.com|$ADMIN_EMAIL|g" alembic/versions/0001_users_table.py
  echo "  ✓ alembic/versions/0001_users_table.py (admin: $ADMIN_EMAIL)"
fi

# ── leftover-placeholder safety check ────────────────────────────────────────
# Surface any unreplaced template tokens so they can be cleaned up before commit.

leftovers=$(grep -rnE '\[PROJECT_NAME\]|\[PROJECT_DESCRIPTION\]|my-project|\bmyapp\b' \
  --include='*.py' --include='*.ts' --include='*.vue' --include='*.md' \
  --include='*.yml' --include='*.yaml' --include='*.toml' \
  --exclude-dir=tmp --exclude-dir=human-instructions \
  --exclude-dir=.venv --exclude-dir=node_modules --exclude-dir=.git \
  . 2>/dev/null || true)

if [[ -n "$leftovers" ]]; then
  echo ""
  echo "⚠  Unreplaced template placeholders detected — review before proceeding:"
  echo "$leftovers" | sed 's/^/    /'
fi

# ── done ─────────────────────────────────────────────────────────────────────

echo ""
echo "Done. Project '$PROJECT_DISPLAY' is ready."
echo ""
echo "Next steps:"
echo ""
echo "  1. Review .env — adjust any values if needed."
echo ""
echo "  2. Configure GitHub Secrets in your repository settings:"
echo "       VPS_HOST      IP address or domain of your VPS"
echo "       VPS_USER      SSH user (e.g. deploy)"
echo "       VPS_SSH_KEY   Private SSH key for CI deployment"
echo "       PROJECT_DIR   Absolute path on VPS (e.g. /opt/$PROJECT_SLUG)"
echo ""
echo "  3. Start the dev stack:"
echo "       docker compose up --build"
echo ""
