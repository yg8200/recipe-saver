from datetime import datetime, timezone
from src.core.database import db

# Link table for the many-to-many relation: one row = "this recipe is in this folder".
# The composite primary key makes a duplicate link impossible, and ON DELETE CASCADE means the
# database itself cleans up links when either side is deleted. The recipe is never deleted by a folder.
recipe_folders = db.Table(
    "recipe_folders",
    db.Column("recipe_id", db.Integer, db.ForeignKey("recipes.id", ondelete="CASCADE"), primary_key=True),
    db.Column("folder_id", db.Integer, db.ForeignKey("folders.id", ondelete="CASCADE"), primary_key=True),
)


class Folder(db.Model):
  __tablename__ = "folders"

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(100), unique=True, nullable=False)
  created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

  # backref adds Recipe.folders, so both directions work: folder.recipes and recipe.folders
  recipes = db.relationship("Recipe", secondary=recipe_folders, backref="folders")

  def to_dict(self):
    return {
        "id": self.id,
        "name": self.name,
        "recipe_count": len(self.recipes),
        "created_at": self.created_at.isoformat() if self.created_at else None,
    }
