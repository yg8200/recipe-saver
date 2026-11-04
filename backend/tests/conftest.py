import pytest
from src import create_app
from src.api.add_recepie import RECIPES


@pytest.fixture
def app():
    app = create_app()
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def clean_recipes_db():
    RECIPES.clear()
    yield
    RECIPES.clear()