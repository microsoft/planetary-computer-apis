"""increase size of description field

Revision ID: 774cf7d62398
Revises: 1e5170d852c1
Create Date: 2021-03-18 22:49:45.797621

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '774cf7d62398'
down_revision = '1e5170d852c1'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "collections",
        "description",
        type_=sa.TEXT,
        schema="data"
    )


def downgrade():
    op.alter_column(
        "collections",
        "description",
        type_=sa.VARCHAR(1024),
        schema="data"
    )
