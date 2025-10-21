"""add_description_to_pets

Revision ID: c3f11346f997
Revises: 
Create Date: 2025-10-17 14:21:52.343131

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c3f11346f997'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add description column to pets table
    op.add_column('pets', sa.Column('description', sa.String(500), nullable=True))


def downgrade() -> None:
    # Remove description column from pets table
    op.drop_column('pets', 'description')
