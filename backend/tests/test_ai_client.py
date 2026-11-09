import pytest

from src.services import ai_client


# Checks the OpenAI model is picked in order: service-specific env var, then AI_MODEL_NAME, then the default.
def test_openai_model_resolution(monkeypatch):
    monkeypatch.delenv("AI_MODEL_NAME", raising=False)
    monkeypatch.delenv("OPENAI_CORRECTOR_MODEL", raising=False)
    assert ai_client.get_openai_model("OPENAI_CORRECTOR_MODEL") == "gpt-4o-mini"
    monkeypatch.setenv("AI_MODEL_NAME", "global-model")
    assert ai_client.get_openai_model("OPENAI_CORRECTOR_MODEL") == "global-model"
    monkeypatch.setenv("OPENAI_CORRECTOR_MODEL", "specific-model")
    assert ai_client.get_openai_model("OPENAI_CORRECTOR_MODEL") == "specific-model"


# Checks Gemini uses gemini-3.8-flash by default and GEMINI_MODEL_NAME overrides it.
def test_gemini_model_default_and_override(monkeypatch):
    monkeypatch.delenv("GEMINI_MODEL_NAME", raising=False)
    assert ai_client.get_gemini_model() == "gemini-3.8-flash"
    monkeypatch.setenv("GEMINI_MODEL_NAME", "gemini-other")
    assert ai_client.get_gemini_model() == "gemini-other"


# Checks that creating an OpenAI or Gemini client without an API key raises a clear error.
def test_missing_keys_raise(monkeypatch):
    for var in ("OPENAI_API_KEY", "AI_API_KEY", "GEMINI_API_KEY"):
        monkeypatch.setenv(var, "")
    with pytest.raises(RuntimeError):
        ai_client.get_openai_client()
    with pytest.raises(RuntimeError):
        ai_client.get_gemini_client()


# Checks the Gemini thinking setting: LOW by default, budget 0 for 2.x models, overridable, and DEFAULT disables it.
def test_gemini_thinking_config(monkeypatch):
    monkeypatch.delenv("GEMINI_THINKING_LEVEL", raising=False)
    assert ai_client.get_gemini_thinking_config("gemini-3.8-flash").thinking_level == "LOW"
    assert ai_client.get_gemini_thinking_config("gemini-2.5-flash").thinking_budget == 0
    monkeypatch.setenv("GEMINI_THINKING_LEVEL", "high")
    assert ai_client.get_gemini_thinking_config("gemini-3.8-flash").thinking_level == "HIGH"
    monkeypatch.setenv("GEMINI_THINKING_LEVEL", "default")
    assert ai_client.get_gemini_thinking_config("gemini-3.8-flash") is None
