"""Add payment_method to orders

Revision ID: 416fe29c1724
Revises: 106f80147634
Create Date: 2024-01-09 12:34:56.789012

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '416fe29c1724'
down_revision = '106f80147634'
branch_labels = None
depends_on = None


def upgrade():
    # First add the column as nullable
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.add_column(sa.Column('payment_method', sa.String(length=20), nullable=True))
    
    # Update existing rows
    op.execute("UPDATE orders SET payment_method = 'card' WHERE payment_method IS NULL")
    
    # Then make it non-nullable
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.alter_column('payment_method',
               existing_type=sa.String(length=20),
               nullable=False,
               existing_server_default=None)


def downgrade():
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.drop_column('payment_method')
