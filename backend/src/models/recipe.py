from datetime import datetime, timezone
from src.core.database import db


class Recipe(db.Model):
  __tablename__ = "recipes"

  id = db.Column(db.Integer, primary_key=True)
  title = db.Column(db.String(255), unique=True, nullable=False, index=True)
  ingredients = db.Column(db.JSON, nullable=False)
  instructions = db.Column(db.JSON, nullable=False)
  prep_time_minutes = db.Column(db.Integer, nullable=True)
  cook_time_minutes = db.Column(db.Integer, nullable=True)
  servings = db.Column(db.Integer, nullable=True)
  created_at = db.Column(
      db.DateTime, default=lambda: datetime.now(timezone.utc)
  )

  def to_dict(self):
    return {
        "id": self.id,
        "title": self.title,
        "ingredients": self.ingredients,
        "instructions": self.instructions,
        "prep_time_minutes": self.prep_time_minutes,
        "cook_time_minutes": self.cook_time_minutes,
        "servings": self.servings,
        "created_at": self.created_at.isoformat() if self.created_at else None,
    }