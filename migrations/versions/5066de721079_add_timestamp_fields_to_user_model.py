"""Add timestamp fields to User model

Revision ID: 5066de721079
Revises: ebf5b354cc58
Create Date: 2024-11-27 02:18:39.227686

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5066de721079'
down_revision = 'ebf5b354cc58'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('date_created', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('date_updated', sa.DateTime(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('date_updated')
        batch_op.drop_column('date_created')

    # ### end Alembic commands ###
