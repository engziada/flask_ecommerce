"""Fix model relationships

Revision ID: 062f7247b72d
Revises: 8b33bb49f01f
Create Date: 2024-11-25 20:12:05.860434

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '062f7247b72d'
down_revision = '8b33bb49f01f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('reviews', schema=None) as batch_op:
        batch_op.add_column(sa.Column('updated_at', sa.DateTime(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('reviews', schema=None) as batch_op:
        batch_op.drop_column('updated_at')

    # ### end Alembic commands ###
