"""Add stripe_payment_id to orders

Revision ID: fa4c90a3087f
Revises: 8e53d4f7833d
Create Date: 2024-11-27 12:30:40.361620

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fa4c90a3087f'
down_revision = '8e53d4f7833d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.add_column(sa.Column('stripe_payment_id', sa.String(length=100), nullable=True))
        batch_op.create_unique_constraint('uq_order_stripe_payment_id', ['stripe_payment_id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.drop_constraint('uq_order_stripe_payment_id', type_='unique')
        batch_op.drop_column('stripe_payment_id')

    # ### end Alembic commands ###
