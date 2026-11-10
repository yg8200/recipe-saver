from flask_migrate import upgrade
from src import create_app
from src.models.recipe import Recipe  # Ensures Recipe is registered with SQLAlchemy

app = create_app()

if __name__ == "__main__":
    with app.app_context():
        # Bring the database schema up to date. Unlike db.create_all() this also ADDS new columns
        # to tables that already exist (see backend/migrations/).
        upgrade()

    app.run(host="0.0.0.0", port=5001, debug=True)