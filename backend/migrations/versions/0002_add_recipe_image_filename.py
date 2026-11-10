"""Add recipes.image_filename for the dish photo.

Revision ID: 0002
Revises: 0001
"""
import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    columns = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("recipes")}
    if "image_filename" not in columns:
        op.add_column("recipes", sa.Column("image_filename", sa.String(100), nullable=True))


def downgrade():
    op.drop_column("recipes", "image_filename")
