"""add_google_id_to_users

Revision ID: 44d65d1d19fa
Revises: b7a80cf1fb75
Create Date: 2025-10-29 20:09:10.546080

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '44d65d1d19fa'
down_revision = 'b7a80cf1fb75'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add google_id column to users table
    op.add_column('users', sa.Column('google_id', sa.String(length=100), nullable=True))
    op.create_index('idx_users_google_id', 'users', ['google_id'], unique=True)


def downgrade() -> None:
    # Remove google_id column from users table
    op.drop_index('idx_users_google_id', table_name='users')
    op.drop_column('users', 'google_id')
