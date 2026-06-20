"""Add api_usage_events for search rate limiting.

Revision ID: 004
Revises: 003
Create Date: 2026-06-20

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: Union[str, Sequence[str], None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "api_usage_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("operator_id", sa.UUID(), nullable=False),
        sa.Column("agent_id", sa.UUID(), nullable=False),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["operator_id"], ["operators.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_api_usage_agent_type_created",
        "api_usage_events",
        ["agent_id", "event_type", "created_at"],
    )
    op.create_index(
        "ix_api_usage_operator_type_created",
        "api_usage_events",
        ["operator_id", "event_type", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_api_usage_operator_type_created", table_name="api_usage_events")
    op.drop_index("ix_api_usage_agent_type_created", table_name="api_usage_events")
    op.drop_table("api_usage_events")
