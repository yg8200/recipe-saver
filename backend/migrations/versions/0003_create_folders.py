"""Create the folders table and the recipe_folders link table.

Idempotent like the earlier migrations: each table is created only when it is missing.

Revision ID: 0003
Revises: 0002
"""
import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table("folders"):
        op.create_table(
            "folders",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(100), nullable=False, unique=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
        )
    if not inspector.has_table("recipe_folders"):
        op.create_table(
            "recipe_folders",
            sa.Column("recipe_id", sa.Integer(), sa.ForeignKey("recipes.id", ondelete="CASCADE"), primary_key=True),
            sa.Column("folder_id", sa.Integer(), sa.ForeignKey("folders.id", ondelete="CASCADE"), primary_key=True),
        )


def downgrade():
    op.drop_table("recipe_folders")
    op.drop_table("folders")
