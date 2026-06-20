"""Initial schema: operators, agents, experiences, capability_tags, experience_tags.

Revision ID: 001
Revises:
Create Date: 2026-06-20

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

experience_status = postgresql.ENUM(
    "draft", "approved", "rejected", name="experience_status", create_type=False
)
experience_visibility = postgresql.ENUM(
    "private", "public", name="experience_visibility", create_type=False
)


def upgrade() -> None:
    experience_status.create(op.get_bind(), checkfirst=True)
    experience_visibility.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "operators",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("github_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("github_id"),
    )

    op.create_table(
        "agents",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("operator_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("model_family", sa.String(length=128), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["operator_id"], ["operators.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "capability_tags",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )

    op.create_table(
        "experiences",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("operator_id", sa.UUID(), nullable=False),
        sa.Column("agent_id", sa.UUID(), nullable=True),
        sa.Column("status", experience_status, server_default="draft", nullable=False),
        sa.Column("visibility", experience_visibility, server_default="private", nullable=False),
        sa.Column("content", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("task", sa.Text(), nullable=False),
        sa.Column("problem", sa.Text(), nullable=False),
        sa.Column("solution", sa.Text(), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=True),
        sa.Column("model_family", sa.String(length=128), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["operator_id"], ["operators.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_experiences_operator_status", "experiences", ["operator_id", "status"])
    op.create_index("ix_experiences_search_problem", "experiences", ["problem"])
    op.create_index("ix_experiences_search_task", "experiences", ["task"])
    op.create_index("ix_experiences_status_visibility", "experiences", ["status", "visibility"])

    op.create_table(
        "experience_tags",
        sa.Column("experience_id", sa.UUID(), nullable=False),
        sa.Column("tag_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["experience_id"], ["experiences.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_id"], ["capability_tags.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("experience_id", "tag_id"),
    )


def downgrade() -> None:
    op.drop_table("experience_tags")
    op.drop_index("ix_experiences_status_visibility", table_name="experiences")
    op.drop_index("ix_experiences_search_task", table_name="experiences")
    op.drop_index("ix_experiences_search_problem", table_name="experiences")
    op.drop_index("ix_experiences_operator_status", table_name="experiences")
    op.drop_table("experiences")
    op.drop_table("capability_tags")
    op.drop_table("agents")
    op.drop_table("operators")
    experience_visibility.drop(op.get_bind(), checkfirst=True)
    experience_status.drop(op.get_bind(), checkfirst=True)
