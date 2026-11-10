import pytest
from src import create_app
from src.core.database import db


@pytest.fixture(autouse=True)
def no_real_ai_calls(monkeypatch):
    """Blank the API keys so any AI call a test forgets to mock fails fast instead of costing money."""
    for var in ("OPENAI_API_KEY", "AI_API_KEY", "GEMINI_API_KEY"):
        monkeypatch.setenv(var, "")


@pytest.fixture(autouse=True)
def no_real_image_downloads(monkeypatch):
    """Tests must never hit the network for dish photos; individual tests opt in by patching again."""
    monkeypatch.setattr("src.services.recipe_image.download_image", lambda url: None)


@pytest.fixture
def app(tmp_path):
    app = create_app("testing")
    app.config["UPLOAD_FOLDER"] = str(tmp_path / "uploads")  # each test gets its own empty folder

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()
        db.engine.dispose()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def jpeg_bytes():
    """A tiny but real JPEG, for tests that store or upload photos."""
    import io
    from PIL import Image

    buffer = io.BytesIO()
    Image.new("RGB", (60, 40), (200, 90, 30)).save(buffer, format="JPEG")
    return buffer.getvalue()
