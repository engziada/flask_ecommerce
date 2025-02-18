"""add paymob fields v2

Revision ID: add_paymob_fields_v2
Revises: 7b47e24ad44d
Create Date: 2025-02-18 02:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_paymob_fields_v2'
down_revision = '7b47e24ad44d'
branch_labels = None
depends_on = None


def upgrade():
    # Add PayMob fields to orders table
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.add_column(sa.Column('paymob_order_id', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('paymob_payment_id', sa.String(length=100), nullable=True))


def downgrade():
    # Remove PayMob fields from orders table
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.drop_column('paymob_payment_id')
        batch_op.drop_column('paymob_order_id')
