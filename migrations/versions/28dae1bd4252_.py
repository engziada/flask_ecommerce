"""empty message

Revision ID: 28dae1bd4252
Revises: 59b0a93df9fb, add_district_to_addresses
Create Date: 2024-12-14 23:57:35.876239

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '28dae1bd4252'
down_revision = ('59b0a93df9fb', 'add_district_to_addresses')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
