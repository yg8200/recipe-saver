"""Add recipes.rating (1-5 stars, NULL = not rated).

Idempotent like the earlier migrations: the column is added only when it is missing.

Revision ID: 0004
Revises: 0003
"""
import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    columns = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("recipes")}
    if "rating" not in columns:
        op.add_column("recipes", sa.Column("rating", sa.SmallInteger(), nullable=True))


def downgrade():
    op.drop_column("recipes", "rating")
