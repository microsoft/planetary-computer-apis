"""Add short_description

Revision ID: 2ef1202a601c
Revises: 774cf7d62398
Create Date: 2021-03-25 21:01:45.375361

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '2ef1202a601c'
down_revision = '774cf7d62398'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "collections",
        sa.Column("short_description", sa.VARCHAR(1024), nullable=True),
        schema="data"
    )

def downgrade():
    op.drop_column(
        "collections",
        "short_description",
        schema="data"
    )
