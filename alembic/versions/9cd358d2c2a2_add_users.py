"""add users

Revision ID: 9cd358d2c2a2
Revises: d96b964ef666
Create Date: 2026-03-19 16:11:59.841387
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = '9cd358d2c2a2'
down_revision: Union[str, Sequence[str], None] = 'd96b964ef666'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # --- CREATE USERS TABLE ---
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    # --- ADD OWNER TO NETWORKS ---
    op.add_column('networks', sa.Column('owner_id', sa.Integer(), nullable=True))

    op.create_index(
        op.f('ix_networks_owner_id'),
        'networks',
        ['owner_id'],
        unique=False
    )

    op.create_foreign_key(
        'fk_networks_owner_id_users',
        'networks',
        'users',
        ['owner_id'],
        ['id']
    )


def downgrade() -> None:
    """Downgrade schema."""

    # --- REMOVE OWNER FROM NETWORKS ---
    op.drop_constraint('fk_networks_owner_id_users', 'networks', type_='foreignkey')
    op.drop_index(op.f('ix_networks_owner_id'), table_name='networks')
    op.drop_column('networks', 'owner_id')

    # --- DROP USERS TABLE ---
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')