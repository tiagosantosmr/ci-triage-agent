import pytest

from agent.llm import get_model


def _clear_all(monkeypatch):
    for key in ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
        monkeypatch.delenv(key, raising=False)


def test_get_model_raises_without_any_key(monkeypatch):
    _clear_all(monkeypatch)
    with pytest.raises(RuntimeError):
        get_model()


def test_get_model_prefers_custom_base_url_when_all_set(monkeypatch):
    _clear_all(monkeypatch)
    monkeypatch.setenv("LLM_BASE_URL", "https://example.com/v1")
    monkeypatch.setenv("LLM_API_KEY", "fake-key")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake")
    model = get_model()
    assert model.__class__.__name__ == "ChatOpenAI"
    assert str(model.openai_api_base) == "https://example.com/v1"


def test_get_model_falls_back_to_openai(monkeypatch):
    _clear_all(monkeypatch)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake")
    model = get_model()
    assert model.__class__.__name__ == "ChatOpenAI"
