import os

# backend/ folder (this file is backend/src/core/config.py)
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class Config:
    """Base configuration with default settings."""
    TESTING = False
    DEBUG = False
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Dish photos are stored as files here; the database only keeps the file name.
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", os.path.join(BACKEND_DIR, "uploads"))
    # Flask rejects bigger request bodies with 413 before our code runs.
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/recipe_saver"
    )


class DevelopmentConfig(Config):
    """Configuration for local development."""
    DEBUG = True


class TestingConfig(Config):
    """Configuration for automated test runs."""
    TESTING = True
    DEBUG = True
    # In-memory SQLite for fast, isolated tests without requiring a running PostgreSQL instance
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class ProductionConfig(Config):
    """Configuration for production deployments."""
    SECRET_KEY = os.getenv("SECRET_KEY")


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}