"""add_departments_and_user_profile_fields

Revision ID: 15b567905a60
Revises: 5dccdbd7aa23
Create Date: 2026-11-22 10:17:24.160490

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '15b567905a60'
down_revision: Union[str, Sequence[str], None] = '5dccdbd7aa23'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'departments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('department_name', sa.String(length=100), nullable=False),
        sa.Column('department_code', sa.String(length=20), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_departments_department_code'), 'departments', ['department_code'], unique=True)
    op.create_index(op.f('ix_departments_department_name'), 'departments', ['department_name'], unique=True)
    op.create_index(op.f('ix_departments_id'), 'departments', ['id'], unique=False)
    op.add_column('users', sa.Column('phone_number', sa.String(length=20), nullable=True))
    op.add_column('users', sa.Column('department_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_users_department_id_departments',
        'users',
        'departments',
        ['department_id'],
        ['id'],
        ondelete='SET NULL',
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('fk_users_department_id_departments', 'users', type_='foreignkey')
    op.drop_column('users', 'department_id')
    op.drop_column('users', 'phone_number')
    op.drop_index(op.f('ix_departments_id'), table_name='departments')
    op.drop_index(op.f('ix_departments_department_name'), table_name='departments')
    op.drop_index(op.f('ix_departments_department_code'), table_name='departments')
    op.drop_table('departments')
