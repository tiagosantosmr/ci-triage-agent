import pytest

from agent.llm import get_model


def test_get_model_raises_without_any_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        get_model()


def test_get_model_prefers_openai_when_both_set(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake")
    model = get_model()
    assert model.__class__.__name__ == "ChatOpenAI"
