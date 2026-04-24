"""Initial schema — users table with default admin seed

Revision ID: 0001
Revises:
Create Date: 2026-01-01

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column(
            "role",
            sa.Enum("admin", "architect", "expert", "ai_agent", name="userrole"),
            nullable=False,
            server_default="architect",
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # Seed default admin user.
    # Password "changeme123" hashed with bcrypt (12 rounds).
    # Generated once so migration is deterministic and doesn't require bcrypt at run time.
    _ADMIN_HASH = "$2b$12$JUH0ENl95Y26jqTeiVPWi.PpsvrCT.ema92b.rd/.bXedDhfsi5mu"
    op.execute(
        sa.text(
            "INSERT INTO users (id, email, hashed_password, role, is_active) "
            "VALUES (gen_random_uuid(), :email, :pw, 'admin', true) "
            "ON CONFLICT (email) DO NOTHING"
        ).bindparams(
            email="admin@example.com",
            pw=_ADMIN_HASH,
        )
    )


def downgrade() -> None:
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS userrole")
