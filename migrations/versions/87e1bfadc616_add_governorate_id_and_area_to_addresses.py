"""Add governorate_id and area to addresses

Revision ID: 87e1bfadc616
Revises: 5615669b3a04
Create Date: 2024-12-11 01:51:04.337518

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '87e1bfadc616'
down_revision = '5615669b3a04'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    # Add governorate_id with a default value of 1 (Cairo)
    with op.batch_alter_table('addresses', schema=None) as batch_op:
        batch_op.add_column(sa.Column('governorate_id', sa.Integer(), server_default='1', nullable=False))
        batch_op.add_column(sa.Column('area', sa.String(length=100), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('addresses', schema=None) as batch_op:
        batch_op.drop_column('area')
        batch_op.drop_column('governorate_id')

    # ### end Alembic commands ###