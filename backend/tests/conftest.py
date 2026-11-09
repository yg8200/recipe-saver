import pytest
from src import create_app
from src.core.database import db


@pytest.fixture(autouse=True)
def no_real_ai_calls(monkeypatch):
    """Blank the API keys so any AI call a test forgets to mock fails fast instead of costing money."""
    for var in ("OPENAI_API_KEY", "AI_API_KEY", "GEMINI_API_KEY"):
        monkeypatch.setenv(var, "")


@pytest.fixture
def app():
    app = create_app("testing")

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()
        db.engine.dispose()


@pytest.fixture
def client(app):
    return app.test_client()
