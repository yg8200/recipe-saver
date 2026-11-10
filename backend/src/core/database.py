from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
# Alembic wrapper: tracks schema changes as versioned scripts in backend/migrations/
migrate = Migrate()