from flask import Flask

def create_app() -> Flask:
    # 1. Create the Flask app instance
    app = Flask(__name__)

    # 2. Import and register blueprints
    from src.api.health import health_bp
    from src.api.add_recipe import add_recipe_bp
    from src.api.delete_recipe import delete_recipe_bp
    
    # All routes in health_bp will be prefixed or mounted here
    app.register_blueprint(health_bp)
    app.register_blueprint(add_recipe_bp)
    app.register_blueprint(delete_recipe_bp)

    return app