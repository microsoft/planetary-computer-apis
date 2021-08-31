"""add collection asset and item_asset columns

Revision ID: 1e5170d852c1
Revises: 131aab4d9e49
Create Date: 2021-03-18 22:36:56.493510

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = '1e5170d852c1'
down_revision = '131aab4d9e49'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "collections",
        sa.Column("assets", JSONB, nullable=True),
        schema="data"
    )
    op.add_column(
        "collections",
        sa.Column("item_assets", JSONB, nullable=True),
        schema="data"
    )



def downgrade():
    op.drop_column(
        "collections",
        "assets",
        schema="data"
    )
    op.drop_column(
        "collections",
        "item_assets",
        schema="data"
    )

