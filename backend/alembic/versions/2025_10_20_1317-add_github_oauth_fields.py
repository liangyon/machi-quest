"""add_github_oauth_fields

Revision ID: add_github_oauth
Revises: c3f11346f997
Create Date: 2025-10-20 13:17:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_github_oauth'
down_revision = 'c3f11346f997'
branch_labels = None
depends_on = None


def upgrade():
    # Add GitHub OAuth fields to users table
    op.add_column('users', sa.Column('github_id', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('github_username', sa.String(length=100), nullable=True))
    op.create_index('ix_users_github_id', 'users', ['github_id'], unique=True)
    
    # Make hashed_password nullable for OAuth-only users
    op.alter_column('users', 'hashed_password',
               existing_type=sa.Text(),
               nullable=True)


def downgrade():
    # Remove GitHub OAuth fields
    op.drop_index('ix_users_github_id', table_name='users')
    op.drop_column('users', 'github_username')
    op.drop_column('users', 'github_id')
    
    # Make hashed_password non-nullable again
    op.alter_column('users', 'hashed_password',
               existing_type=sa.Text(),
               nullable=False)
