"""init

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-07-26 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users
    op.create_table('users',
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('username', sa.String(length=50), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('full_name', sa.String(length=100), nullable=True),
    sa.Column('avatar_url', sa.String(length=255), nullable=True),
    sa.Column('role', sa.String(length=20), nullable=False, server_default='user'),
    sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
    sa.Column('last_login_at', sa.DateTime(), nullable=True),
    sa.Column('bio', sa.String(length=500), nullable=True),
    sa.Column('github_profile', sa.String(length=255), nullable=True),
    sa.Column('linkedin_profile', sa.String(length=255), nullable=True),
    sa.Column('preferred_languages', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_users'))
    )
    op.create_index(op.f('ix_users_created_at'), 'users', ['created_at'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    # 2. languages
    op.create_table('languages',
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('name', sa.String(length=50), nullable=False),
    sa.Column('extension', sa.String(length=20), nullable=False),
    sa.Column('icon', sa.String(length=255), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_languages')),
    sa.UniqueConstraint('name', name=op.f('uq_languages_name'))
    )
    op.create_index(op.f('ix_languages_created_at'), 'languages', ['created_at'], unique=False)

    # 3. reviews
    op.create_table('reviews',
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('language_id', sa.UUID(), nullable=True),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('source_code', sa.Text(), nullable=False),
    sa.Column('improved_code', sa.Text(), nullable=True),
    sa.Column('issues', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
    sa.Column('quality_score', sa.Integer(), nullable=True),
    sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
    sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
    sa.Column('file_name', sa.String(length=255), nullable=True),
    sa.Column('file_size', sa.Integer(), nullable=True),
    sa.Column('repo_url', sa.String(length=1024), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['language_id'], ['languages.id'], name=op.f('fk_reviews_language_id_languages')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_reviews_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_reviews'))
    )
    op.create_index(op.f('ix_reviews_created_at'), 'reviews', ['created_at'], unique=False)
    op.create_index(op.f('ix_reviews_title'), 'reviews', ['title'], unique=False)
    op.create_index(op.f('ix_reviews_repo_url'), 'reviews', ['repo_url'], unique=False)

    # 4. reports
    op.create_table('reports',
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('review_id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('file_path', sa.String(length=1024), nullable=False),
    sa.Column('file_size', sa.Integer(), nullable=False),
    sa.Column('format', sa.String(length=10), nullable=False, server_default='pdf'),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['review_id'], ['reviews.id'], name=op.f('fk_reports_review_id_reviews'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_reports_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_reports'))
    )
    op.create_index(op.f('ix_reports_created_at'), 'reports', ['created_at'], unique=False)

    # 5. favorite_collections
    op.create_table('favorite_collections',
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_favorite_collections_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_favorite_collections'))
    )
    op.create_index(op.f('ix_favorite_collections_created_at'), 'favorite_collections', ['created_at'], unique=False)

    # 6. favorites
    op.create_table('favorites',
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('review_id', sa.UUID(), nullable=False),
    sa.Column('collection_id', sa.UUID(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['collection_id'], ['favorite_collections.id'], name=op.f('fk_favorites_collection_id_favorite_collections'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['review_id'], ['reviews.id'], name=op.f('fk_favorites_review_id_reviews'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_favorites_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_favorites')),
    sa.UniqueConstraint('user_id', 'review_id', name='uq_user_review_favorite')
    )
    op.create_index(op.f('ix_favorites_created_at'), 'favorites', ['created_at'], unique=False)

    # 7. settings
    op.create_table('settings',
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('theme', sa.String(length=20), nullable=False, server_default='system'),
    sa.Column('email_notifications', sa.Boolean(), nullable=False, server_default='true'),
    sa.Column('default_language', sa.String(length=50), nullable=True),
    sa.Column('preferences', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_settings_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_settings')),
    sa.UniqueConstraint('user_id', name=op.f('uq_settings_user_id'))
    )
    op.create_index(op.f('ix_settings_created_at'), 'settings', ['created_at'], unique=False)

    # 8. audit_logs
    op.create_table('audit_logs',
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=True),
    sa.Column('action', sa.String(length=255), nullable=False),
    sa.Column('resource_type', sa.String(length=100), nullable=False),
    sa.Column('resource_id', sa.String(length=255), nullable=True),
    sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
    sa.Column('ip_address', sa.String(length=45), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_audit_logs_user_id_users'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_audit_logs'))
    )
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'], unique=False)
    op.create_index(op.f('ix_audit_logs_created_at'), 'audit_logs', ['created_at'], unique=False)
    op.create_index('ix_audit_logs_resource', 'audit_logs', ['resource_type', 'resource_id'], unique=False)
    op.create_index('ix_audit_logs_user_created', 'audit_logs', ['user_id', 'created_at'], unique=False)


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('settings')
    op.drop_table('favorites')
    op.drop_table('favorite_collections')
    op.drop_table('reports')
    op.drop_table('reviews')
    op.drop_table('languages')
    op.drop_table('users')
