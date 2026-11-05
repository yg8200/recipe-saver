from src import create_app
from src.core.database import db
from src.models.recipe import Recipe  # Ensures Recipe is registered with SQLAlchemy

app = create_app()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(host="0.0.0.0", port=5001, debug=True)