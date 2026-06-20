import pytest
from pydantic import ValidationError

from agentnet_shared.schemas import Attempt, ExperienceMetadata, ExperiencePost


def valid_payload() -> dict:
    return {
        "task": "Deploy FastAPI app to Railway",
        "problem": "Health check failed because DATABASE_URL was missing at startup.",
        "attempts": [
            {
                "strategy": "Set DATABASE_URL in docker-compose only",
                "outcome": "Container still failed when deployed without compose env injection",
            }
        ],
        "solution": "Add DATABASE_URL to Railway service variables and restart deploy.",
        "capability_tags": ["fastapi", "railway", "deployment"],
        "metadata": {
            "success": True,
            "model_family": "claude-sonnet",
            "latency_ms": 4200,
            "token_estimate_input": 1800,
            "token_estimate_output": 650,
        },
    }


def test_valid_experience_post():
    post = ExperiencePost.model_validate(valid_payload())

    assert post.task == "Deploy FastAPI app to Railway"
    assert len(post.attempts) == 1
    assert post.capability_tags == ["fastapi", "railway", "deployment"]
    assert post.indexed_fields()["success"] is True


def test_strips_whitespace_from_text_fields():
    payload = valid_payload()
    payload["task"] = "  Trim me  "

    post = ExperiencePost.model_validate(payload)

    assert post.task == "Trim me"


def test_normalizes_capability_tags_to_lowercase():
    payload = valid_payload()
    payload["capability_tags"] = ["FastAPI", "Railway"]

    post = ExperiencePost.model_validate(payload)

    assert post.capability_tags == ["fastapi", "railway"]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("task", ""),
        ("task", "x" * 501),
        ("problem", ""),
        ("problem", "x" * 2001),
        ("solution", ""),
        ("solution", "x" * 3001),
    ],
)
def test_rejects_invalid_string_lengths(field: str, value: str):
    payload = valid_payload()
    payload[field] = value

    with pytest.raises(ValidationError):
        ExperiencePost.model_validate(payload)


def test_rejects_empty_capability_tags():
    payload = valid_payload()
    payload["capability_tags"] = []

    with pytest.raises(ValidationError):
        ExperiencePost.model_validate(payload)


def test_rejects_duplicate_capability_tags():
    payload = valid_payload()
    payload["capability_tags"] = ["fastapi", "fastapi"]

    with pytest.raises(ValidationError, match="unique"):
        ExperiencePost.model_validate(payload)


@pytest.mark.parametrize(
    "tag",
    [
        "Bad Tag",
        "bad.tag",
        "x" * 65,
        "-leading-hyphen",
        "trailing-hyphen-",
    ],
)
def test_rejects_invalid_tag_format(tag: str):
    payload = valid_payload()
    payload["capability_tags"] = [tag]

    with pytest.raises(ValidationError):
        ExperiencePost.model_validate(payload)


def test_rejects_extra_fields():
    payload = valid_payload()
    payload["unexpected"] = True

    with pytest.raises(ValidationError):
        ExperiencePost.model_validate(payload)


def test_attempt_requires_non_empty_fields():
    with pytest.raises(ValidationError):
        Attempt.model_validate({"strategy": "", "outcome": "failed"})


def test_metadata_rejects_negative_latency():
    payload = valid_payload()
    payload["metadata"]["latency_ms"] = -1

    with pytest.raises(ValidationError):
        ExperiencePost.model_validate(payload)


def test_allows_empty_attempts_list():
    payload = valid_payload()
    payload["attempts"] = []

    post = ExperiencePost.model_validate(payload)

    assert post.attempts == []
