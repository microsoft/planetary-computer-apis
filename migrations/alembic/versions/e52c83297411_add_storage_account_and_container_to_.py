"""add storage account and container to collection

Revision ID: e52c83297411
Revises: 2ef1202a601c
Create Date: 2021-04-03 22:20:31.606348

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'e52c83297411'
down_revision = '2ef1202a601c'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "collections",
        sa.Column("storage_account", sa.VARCHAR(63), nullable=True),
        schema="data"
    )
    op.add_column(
        "collections",
        sa.Column("container", sa.VARCHAR(63), nullable=True),
        schema="data"
    )

def downgrade():
    op.drop_column(
        "collections",
        "storage_account",
        schema="data"
    )
    op.drop_column(
        "collections",
        "container",
        schema="data"
    )
