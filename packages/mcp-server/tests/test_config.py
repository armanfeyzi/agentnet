import pytest

from agentnet_mcp.config import AgentNetSettings


def test_settings_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENTNET_API_KEY", "test-key")
    monkeypatch.setenv("AGENTNET_AGENT_ID", "agent-123")
    monkeypatch.setenv("AGENTNET_API_URL", "http://api.example/")

    settings = AgentNetSettings()

    assert settings.api_key == "test-key"
    assert settings.agent_id == "agent-123"
    assert settings.api_url == "http://api.example/"


def test_settings_default_api_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENTNET_API_KEY", "test-key")
    monkeypatch.setenv("AGENTNET_AGENT_ID", "agent-123")
    monkeypatch.delenv("AGENTNET_API_URL", raising=False)

    settings = AgentNetSettings()

    assert settings.api_url == "http://localhost:8000"


def test_settings_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AGENTNET_API_KEY", raising=False)
    monkeypatch.setenv("AGENTNET_AGENT_ID", "agent-123")

    with pytest.raises(Exception):
        AgentNetSettings()


def test_auth_headers(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENTNET_API_KEY", "secret")
    monkeypatch.setenv("AGENTNET_AGENT_ID", "agent-456")

    settings = AgentNetSettings()

    assert settings.auth_headers == {
        "X-API-Key": "secret",
        "X-Agent-ID": "agent-456",
    }
