"""add district to addresses

Revision ID: add_district_to_addresses
Revises: 
Create Date: 2024-12-14 03:04:39.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_district_to_addresses'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add district column to addresses table
    op.add_column('addresses', sa.Column('district', sa.String(length=100), nullable=True))


def downgrade():
    # Remove district column from addresses table
    op.drop_column('addresses', 'district')
