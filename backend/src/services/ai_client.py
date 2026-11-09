"""Shared AI client factories and model settings used by all extraction services."""
import os

from dotenv import load_dotenv
from google import genai
from openai import OpenAI

load_dotenv()

DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"


def get_openai_client() -> OpenAI:
    # AI_API_KEY / AI_BASE_URL allow pointing at any OpenAI-compatible provider.
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("AI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set in your .env file.")
    return OpenAI(api_key=api_key, base_url=os.getenv("AI_BASE_URL") or None)


def get_openai_model(env_var: str | None = None, default: str = DEFAULT_OPENAI_MODEL) -> str:
    """Model for a specific service (env_var), falling back to AI_MODEL_NAME, then default."""
    return (env_var and os.getenv(env_var)) or os.getenv("AI_MODEL_NAME") or default


def get_gemini_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set in your .env file.")
    # v1beta is required for JSON response mode
    return genai.Client(api_key=api_key, http_options={"api_version": "v1beta"})


def get_gemini_model() -> str:
    return os.getenv("GEMINI_MODEL_NAME") or DEFAULT_GEMINI_MODEL
