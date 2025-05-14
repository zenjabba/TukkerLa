"""Add Google OAuth fields to User model

Revision ID: add_google_oauth_fields
Revises: 
Create Date: 2024-06-02

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = 'add_google_oauth_fields'
down_revision = None  # Set to the previous migration if there is one
branch_labels = None
depends_on = None


def upgrade():
    # Make password_hash nullable to support OAuth users
    op.alter_column('users', 'password_hash', 
                    existing_type=sa.String(100),
                    nullable=True)
    
    # Add Google OAuth fields
    op.add_column('users', sa.Column('google_id', sa.String(100), nullable=True, unique=True))
    op.add_column('users', sa.Column('picture', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('auth_provider', sa.String(20), nullable=False, server_default='local'))


def downgrade():
    # Drop Google OAuth fields
    op.drop_column('users', 'auth_provider')
    op.drop_column('users', 'picture')
    op.drop_column('users', 'google_id')
    
    # Make password_hash non-nullable again
    op.alter_column('users', 'password_hash', 
                    existing_type=sa.String(100),
                    nullable=False) 