"""Add capability_tags and api_key_scope to agents.

Revision ID: 002
Revises: 001
Create Date: 2026-06-20

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, Sequence[str], None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "agents",
        sa.Column(
            "capability_tags",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column(
        "agents",
        sa.Column(
            "api_key_scope",
            sa.String(length=32),
            nullable=False,
            server_default="operator",
        ),
    )


def downgrade() -> None:
    op.drop_column("agents", "api_key_scope")
    op.drop_column("agents", "capability_tags")
