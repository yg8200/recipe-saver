from flask_migrate import upgrade
from src import create_app
from src.models.recipe import Recipe  # Ensures the models are registered with SQLAlchemy
from src.models.folder import Folder

app = create_app()

if __name__ == "__main__":
    with app.app_context():
        # Migrations, not create_all(): create_all() never adds columns to existing tables
        upgrade()

    app.run(host="0.0.0.0", port=5001, debug=True)