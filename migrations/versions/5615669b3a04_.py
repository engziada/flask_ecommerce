"""empty message

Revision ID: 5615669b3a04
Revises: add_coupon_table, f4fd87c101da
Create Date: 2024-12-08 03:51:59.313132

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5615669b3a04'
down_revision = ('add_coupon_table', 'f4fd87c101da')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
