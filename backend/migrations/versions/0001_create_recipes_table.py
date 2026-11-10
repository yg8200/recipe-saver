"""Create the recipes table.

The app used to build its schema with db.create_all(), so existing databases already have this table
but no Alembic history. This migration is therefore idempotent: it creates the table only when it
is missing. A fresh database gets it created; an existing one is simply adopted into Alembic.

Revision ID: 0001
Revises:
"""
import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    if sa.inspect(op.get_bind()).has_table("recipes"):
        return
    op.create_table(
        "recipes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("ingredients", sa.JSON(), nullable=False),
        sa.Column("instructions", sa.JSON(), nullable=False),
        sa.Column("prep_time_minutes", sa.Integer(), nullable=True),
        sa.Column("cook_time_minutes", sa.Integer(), nullable=True),
        sa.Column("servings", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_recipes_title", "recipes", ["title"], unique=True)


def downgrade():
    op.drop_index("ix_recipes_title", table_name="recipes")
    op.drop_table("recipes")
