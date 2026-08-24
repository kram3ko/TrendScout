"""add amazon categories

Revision ID: c2d7f65a31e8
Revises: 8e1eb29cbbfa
Create Date: 2026-08-24 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c2d7f65a31e8"
down_revision: str | Sequence[str] | None = "8e1eb29cbbfa"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "amazon_categories",
        sa.Column("slug", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("available", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
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
    )
    op.create_index(
        op.f("ix_amazon_categories_enabled"), "amazon_categories", ["enabled"], unique=False
    )
    op.create_index(
        op.f("ix_amazon_categories_slug"), "amazon_categories", ["slug"], unique=True
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_amazon_categories_slug"), table_name="amazon_categories")
    op.drop_index(op.f("ix_amazon_categories_enabled"), table_name="amazon_categories")
    op.drop_table("amazon_categories")
