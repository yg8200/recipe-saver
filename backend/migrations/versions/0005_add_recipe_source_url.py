"""Add recipes.source_url (the link a recipe was extracted from, NULL = none).

Idempotent like the earlier migrations: the column is added only when it is missing.

Revision ID: 0005
Revises: 0004
"""
import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade():
    columns = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("recipes")}
    if "source_url" not in columns:
        op.add_column("recipes", sa.Column("source_url", sa.String(2048), nullable=True))


def downgrade():
    op.drop_column("recipes", "source_url")
