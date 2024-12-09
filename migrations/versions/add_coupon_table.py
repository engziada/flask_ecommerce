"""Add coupon table

Revision ID: add_coupon_table
Revises: 
Create Date: 2024-12-08 03:47:47.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_coupon_table'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('coupons',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=20), nullable=False),
        sa.Column('discount_type', sa.String(length=20), nullable=False),
        sa.Column('discount_amount', sa.Float(), nullable=False),
        sa.Column('min_purchase_amount', sa.Float(), nullable=True),
        sa.Column('max_discount_amount', sa.Float(), nullable=True),
        sa.Column('valid_from', sa.DateTime(), nullable=False),
        sa.Column('valid_until', sa.DateTime(), nullable=True),
        sa.Column('usage_limit', sa.Integer(), nullable=True),
        sa.Column('times_used', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )


def downgrade():
    op.drop_table('coupons')
