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
REDIS_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(24))")

# ── banner ────────────────────────────────────────────────────────────────────

echo ""
echo "Initialising project: $PROJECT_DISPLAY"
echo "  Slug:   $PROJECT_SLUG"
echo "  DB:     $DB_NAME"
echo "  Domain: $DOMAIN"
echo "  Admin:  $ADMIN_EMAIL"
echo ""

# ── create .env ───────────────────────────────────────────────────────────────

cp .env.example .env

# Replace DB name (handles both POSTGRES_DB=myapp and myapp in DATABASE_URL)
sedi "s|myapp|$DB_NAME|g" .env
# Replace passwords — order matters: more specific patterns first
sedi "s|changeme_redis|$REDIS_PASSWORD|g" .env
sedi "s|changeme|$DB_PASSWORD|g" .env
sedi "s|CHANGE_ME_generate_a_secure_random_hex_string|$SECRET_KEY|g" .env
# Replace domain placeholders
sedi "s|\[DOMAIN\]|$DOMAIN|g" .env
# Replace project name comment
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

sedi "s|title=\"\[PROJECT_NAME\]\"|title=\"$PROJECT_DISPLAY\"|g" app/main.py
sedi "s|\[PROJECT_DESCRIPTION\]||g" app/main.py
echo "  ✓ app/main.py"

# ── frontend ──────────────────────────────────────────────────────────────────

sedi "s|\[PROJECT_NAME\]|$PROJECT_DISPLAY|g" frontend/app/layouts/default.vue
sedi "s|\[PROJECT_NAME\]|$PROJECT_DISPLAY|g" frontend/app/pages/dashboard.vue
sedi "s|\[PROJECT_NAME\]|$PROJECT_DISPLAY|g" frontend/app/pages/login.vue
echo "  ✓ frontend/"

# ── nginx/nginx.conf ──────────────────────────────────────────────────────────

sedi "s|\[DOMAIN\]|$DOMAIN|g" nginx/nginx.conf
echo "  ✓ nginx/nginx.conf"

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
