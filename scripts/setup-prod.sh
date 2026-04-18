#!/usr/bin/env bash
# setup-prod.sh — generate a production-ready .env on the VPS.
# Run this once after cloning the repository onto your server.
#
# Usage:
#   ./scripts/setup-prod.sh <domain> [admin-email]
#
# Arguments:
#   domain         production domain without protocol, e.g. example.com
#   admin-email    optional; default: admin@<domain>
#
# Example:
#   ./scripts/setup-prod.sh helpformedicine.ru admin@helpformedicine.ru

set -euo pipefail

# ── helpers ────────────────────────────────────────────────────────────────────

usage() {
  sed -n '2,13p' "$0" | sed 's/^# \{0,1\}//'
  exit 0
}

die() { echo "Error: $*" >&2; exit 1; }

sedi() {
  if [[ "$(uname)" == "Darwin" ]]; then
    sed -i '' "$@"
  else
    sed -i "$@"
  fi
}

# ── argument handling ──────────────────────────────────────────────────────────

[[ "${1:-}" =~ ^(-h|--help)$ ]] && usage
[[ $# -lt 1 ]] && { echo "Error: domain argument required."; echo; usage; }

DOMAIN="${1#http://}"
DOMAIN="${DOMAIN#https://}"
DOMAIN="${DOMAIN%/}"
ADMIN_EMAIL="${2:-admin@$DOMAIN}"

[[ "$DOMAIN" =~ ^[a-zA-Z0-9]([a-zA-Z0-9.-]*[a-zA-Z0-9])?$ ]] \
  || die "domain must be a bare hostname without protocol (e.g. example.com). Got: '$DOMAIN'"

# ── locate project root ────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$ROOT_DIR"

# ── preflight ─────────────────────────────────────────────────────────────────

[[ -f .env.example ]] || die ".env.example not found. Make sure you are in the project root."
command -v python3 &>/dev/null || die "python3 is required to generate secrets."

# ── idempotency guard ─────────────────────────────────────────────────────────

if [[ -f .env ]]; then
  echo "Warning: .env already exists."
  read -r -p "Overwrite with a fresh production configuration? [y/N] " confirm
  [[ "$confirm" =~ ^[Yy]$ ]] || exit 0
fi

# ── generate secrets ──────────────────────────────────────────────────────────

SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
DB_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(24))")
REDIS_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(24))")

# ── banner ────────────────────────────────────────────────────────────────────

echo ""
echo "Configuring production environment"
echo "  Domain: $DOMAIN"
echo "  Admin:  $ADMIN_EMAIL"
echo ""

# ── create .env ───────────────────────────────────────────────────────────────

cp .env.example .env

# Replace secrets (order matters: more specific pattern first)
sedi "s|changeme_redis|$REDIS_PASSWORD|g" .env
sedi "s|changeme|$DB_PASSWORD|g" .env
sedi "s|CHANGE_ME_generate_a_secure_random_hex_string|$SECRET_KEY|g" .env

# Replace domain placeholder
sedi "s|\[DOMAIN\]|$DOMAIN|g" .env

# Production-specific values
sedi "s|^APP_ENV=.*|APP_ENV=production|" .env
sedi "s|^NUXT_PUBLIC_API_BASE=.*|NUXT_PUBLIC_API_BASE=https://$DOMAIN|" .env
# Note: no /api suffix — adding it causes double-prefix (/api/api/...) in browser requests
sedi 's|^CORS_ORIGINS=.*|CORS_ORIGINS=["https://'"$DOMAIN"'","https://www.'"$DOMAIN"'"]|' .env

echo "  ✓ .env created"

# ── nginx/nginx.conf ──────────────────────────────────────────────────────────

if grep -q '\[DOMAIN\]' nginx/nginx.conf 2>/dev/null; then
  sedi "s|\[DOMAIN\]|$DOMAIN|g" nginx/nginx.conf
  echo "  ✓ nginx/nginx.conf"
fi

# ── docker-compose.override.yml ───────────────────────────────────────────────

if [[ -f docker-compose.override.yml ]]; then
  rm docker-compose.override.yml
  echo "  ✓ docker-compose.override.yml removed (dev-only)"
fi

# ── done ──────────────────────────────────────────────────────────────────────

echo ""
echo "Done. Production .env is ready."
echo ""
echo "Generated secrets (shown once — already saved to .env):"
echo "  POSTGRES_PASSWORD: $DB_PASSWORD"
echo "  REDIS_PASSWORD:    $REDIS_PASSWORD"
echo "  SECRET_KEY:        $SECRET_KEY"
echo ""
echo "Next steps:"
echo ""
echo "  1. Verify DNS resolves to this server:"
echo "       nslookup $DOMAIN"
echo ""
echo "  2. Issue SSL certificate (run BEFORE starting the stack — port 80 must be free):"
echo "       docker run --rm -p 80:80 \\"
echo "         -v /etc/letsencrypt:/etc/letsencrypt \\"
echo "         certbot/certbot certonly --standalone \\"
echo "         -d $DOMAIN -d www.$DOMAIN \\"
echo "         --email $ADMIN_EMAIL --agree-tos --no-eff-email"
echo ""
echo "  3. Start the stack:"
echo "       docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build"
echo ""
