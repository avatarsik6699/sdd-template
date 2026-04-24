{
  "_meta": {
    "version": "v1.0",
    "format": "SDD CONTEXT.md — Single Source of Truth for AI agent",
    "update_rule": "Bump version on schema/API/type changes. Use /context-update skill after each phase.",
    "version_scheme": "patch (v1.0→v1.1) = additive only; minor (v1.1→v1.2) = breaking change"
  },

  "captured_at": "[DATE]",
  "phase_completed": null,
  "phase_in_progress": null,

  "stack": {
    "db_engine": "PostgreSQL 18 alpine",
    "orm": "SQLAlchemy 2.0 async",
    "backend": "FastAPI / Pydantic v2 / Python 3.13+",
    "frontend": "React 19 / React Router 7 SSR / TypeScript / pnpm",
    "cache": "Redis 8",
    "auth": "JWT (HS256), bcrypt",
    "infra": "Docker Compose, Alembic migrations, uv package manager"
  },

  "core_models": [
    "User (id UUID PK, email UNIQUE, hashed_password, role ENUM[admin/architect/expert/ai_agent], is_active, created_at, updated_at)"
  ],

  "endpoints_active": [
    "GET  /api/v1/health",
    "POST /api/v1/auth/login  — email+password → JWT access_token",
    "GET  /api/v1/auth/me     — current user (JWT required)",
    "POST /api/v1/auth/logout — stateless stub (JWT required)"
  ],

  "db_schema": {
    "tables": ["users"],
    "source": "alembic_versions",
    "current_head": "0001_users_table"
  },

  "ui_pages_active": [
    "/login     — auth form (blank layout)",
    "/dashboard — stub (default layout, JWT required)"
  ],

  "env_config": {
    "keys": [
      "DATABASE_URL", "POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB",
      "REDIS_URL", "SECRET_KEY", "ALGORITHM", "ACCESS_TOKEN_EXPIRE_MINUTES",
      "CORS_ORIGINS", "APP_ENV", "LOG_LEVEL", "API_BASE_URL"
    ]
  },

  "db_seeds": {
    "default_admin": "admin@example.com / changeme123 (migration 0001)"
  },

  "notes": "Initial template state. Run /context-update N after each phase is completed."
}
