import pytest

from src.services import ai_client


def test_openai_model_resolution(monkeypatch):
    monkeypatch.delenv("AI_MODEL_NAME", raising=False)
    monkeypatch.delenv("OPENAI_CORRECTOR_MODEL", raising=False)
    assert ai_client.get_openai_model("OPENAI_CORRECTOR_MODEL") == "gpt-4o-mini"
    monkeypatch.setenv("AI_MODEL_NAME", "global-model")
    assert ai_client.get_openai_model("OPENAI_CORRECTOR_MODEL") == "global-model"
    monkeypatch.setenv("OPENAI_CORRECTOR_MODEL", "specific-model")
    assert ai_client.get_openai_model("OPENAI_CORRECTOR_MODEL") == "specific-model"


def test_gemini_model_default_and_override(monkeypatch):
    monkeypatch.delenv("GEMINI_MODEL_NAME", raising=False)
    assert ai_client.get_gemini_model() == "gemini-2.5-flash"
    monkeypatch.setenv("GEMINI_MODEL_NAME", "gemini-other")
    assert ai_client.get_gemini_model() == "gemini-other"


def test_missing_keys_raise(monkeypatch):
    for var in ("OPENAI_API_KEY", "AI_API_KEY", "GEMINI_API_KEY"):
        monkeypatch.setenv(var, "")
    with pytest.raises(RuntimeError):
        ai_client.get_openai_client()
    with pytest.raises(RuntimeError):
        ai_client.get_gemini_client()
