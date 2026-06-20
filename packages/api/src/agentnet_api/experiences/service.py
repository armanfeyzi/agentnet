from sqlalchemy import select
from sqlalchemy.orm import Session

from agentnet_api.db.models import CapabilityTag, Experience
from agentnet_shared.schemas.experience import ExperiencePost


def resolve_capability_tags(db: Session, tag_slugs: list[str]) -> list[CapabilityTag]:
    db_tags: list[CapabilityTag] = []
    for tag_slug in tag_slugs:
        db_tag = db.scalar(select(CapabilityTag).where(CapabilityTag.slug == tag_slug))
        if not db_tag:
            db_tag = CapabilityTag(slug=tag_slug)
            db.add(db_tag)
            db.flush()
        db_tags.append(db_tag)
    return db_tags


def apply_experience_post(experience: Experience, post: ExperiencePost, db: Session) -> None:
    experience.content = post.model_dump()
    for field, value in post.indexed_fields().items():
        setattr(experience, field, value)
    experience.tags = resolve_capability_tags(db, post.capability_tags)
