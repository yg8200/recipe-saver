import os
from flask import Flask
from src.core.config import config_by_name
from src.core.database import db
from src.api.health import health_bp
from src.api.add_recipe import add_recipe_bp
from src.api.delete_recipe import delete_recipe_bp
from src.api.change_recipe import change_recipe_bp
from src.api.get_recipe import get_recipe_bp


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__)

    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    app.config.from_object(config_by_name[config_name])

    db.init_app(app)

    app.register_blueprint(health_bp)
    app.register_blueprint(add_recipe_bp)
    app.register_blueprint(delete_recipe_bp)
    app.register_blueprint(change_recipe_bp)
    app.register_blueprint(get_recipe_bp)

    return app