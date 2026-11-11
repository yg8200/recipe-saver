import os
from flask import Flask, jsonify
from src.core.config import config_by_name
from src.core.config import BACKEND_DIR
from src.core.database import db, migrate
from src.api.health import health_bp
from src.api.add_recipe import add_recipe_bp
from src.api.delete_recipe import delete_recipe_bp
from src.api.change_recipe import change_recipe_bp
from src.api.get_recipe import get_recipe_bp
from src.api.extract_recipe import extract_recipe_bp
from src.api.upload_recipe import upload_recipe_bp
from src.api.recipe_image import recipe_image_bp
from src.api.folders import folders_bp

def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__)

    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    app.config.from_object(config_by_name[config_name])

    db.init_app(app)
    migrate.init_app(app, db, directory=os.path.join(BACKEND_DIR, "migrations"))

    app.register_blueprint(health_bp)
    app.register_blueprint(add_recipe_bp)
    app.register_blueprint(delete_recipe_bp)
    app.register_blueprint(change_recipe_bp)
    app.register_blueprint(get_recipe_bp)
    app.register_blueprint(extract_recipe_bp)
    app.register_blueprint(upload_recipe_bp)
    app.register_blueprint(recipe_image_bp)
    app.register_blueprint(folders_bp)

    @app.errorhandler(413)
    def too_large(_error):
        return jsonify({"error": "The uploaded file is too large (16 MB maximum)."}), 413

    app.json.ensure_ascii = False

    return app