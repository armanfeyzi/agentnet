import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from agentnet_api.db.base import Base


class ExperienceStatus(str, enum.Enum):
    draft = "draft"
    approved = "approved"
    rejected = "rejected"


class ExperienceVisibility(str, enum.Enum):
    private = "private"
    public = "public"


class Operator(Base):
    __tablename__ = "operators"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str | None] = mapped_column(String(320), unique=True, nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    github_id: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    agents: Mapped[list["Agent"]] = relationship(back_populates="operator")
    experiences: Mapped[list["Experience"]] = relationship(back_populates="operator")


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    operator_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("operators.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    model_family: Mapped[str | None] = mapped_column(String(128), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    operator: Mapped["Operator"] = relationship(back_populates="agents")
    experiences: Mapped[list["Experience"]] = relationship(back_populates="agent")


class CapabilityTag(Base):
    __tablename__ = "capability_tags"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    experiences: Mapped[list["Experience"]] = relationship(
        secondary="experience_tags", back_populates="tags"
    )


class Experience(Base):
    __tablename__ = "experiences"
    __table_args__ = (
        Index("ix_experiences_status_visibility", "status", "visibility"),
        Index("ix_experiences_operator_status", "operator_id", "status"),
        Index("ix_experiences_search_task", "task"),
        Index("ix_experiences_search_problem", "problem"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    operator_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("operators.id", ondelete="CASCADE"), nullable=False
    )
    agent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[ExperienceStatus] = mapped_column(
        Enum(ExperienceStatus, name="experience_status"),
        nullable=False,
        server_default=ExperienceStatus.draft.value,
    )
    visibility: Mapped[ExperienceVisibility] = mapped_column(
        Enum(ExperienceVisibility, name="experience_visibility"),
        nullable=False,
        server_default=ExperienceVisibility.private.value,
    )
    content: Mapped[dict] = mapped_column(JSONB, nullable=False)
    task: Mapped[str] = mapped_column(Text, nullable=False)
    problem: Mapped[str] = mapped_column(Text, nullable=False)
    solution: Mapped[str] = mapped_column(Text, nullable=False)
    success: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    model_family: Mapped[str | None] = mapped_column(String(128), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    operator: Mapped["Operator"] = relationship(back_populates="experiences")
    agent: Mapped["Agent | None"] = relationship(back_populates="experiences")
    tags: Mapped[list["CapabilityTag"]] = relationship(
        secondary="experience_tags", back_populates="experiences"
    )


class ExperienceTag(Base):
    __tablename__ = "experience_tags"

    experience_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("experiences.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("capability_tags.id", ondelete="CASCADE"), primary_key=True
    )
