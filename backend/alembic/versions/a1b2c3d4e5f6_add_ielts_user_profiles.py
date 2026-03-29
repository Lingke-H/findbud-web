"""add_ielts_user_profiles

Revision ID: a1b2c3d4e5f6
Revises: 9208edf71e58
Create Date: 2026-03-29 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '9208edf71e58'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'ielts_user_profiles',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('skill_listening',        sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column('skill_reading',          sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column('skill_writing',          sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column('skill_speaking',         sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column('personality_planner',     sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column('personality_resourcer',   sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column('personality_coordinator', sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column('strength_fluency',          sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column('strength_has_ielts_exp',    sa.Boolean(), nullable=True),
        sa.Column('strength_willing_training', sa.Boolean(), nullable=True),
        sa.Column('strength_weekly_hours',     sa.Integer(), nullable=True),
        sa.Column('strength_target_score',     sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column('preferred_role', sa.String(length=20), nullable=True),
        sa.Column('raw_answers', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('skill_listening        BETWEEN 0 AND 10', name='ck_ielts_skill_listening'),
        sa.CheckConstraint('skill_reading          BETWEEN 0 AND 10', name='ck_ielts_skill_reading'),
        sa.CheckConstraint('skill_writing          BETWEEN 0 AND 10', name='ck_ielts_skill_writing'),
        sa.CheckConstraint('skill_speaking         BETWEEN 0 AND 10', name='ck_ielts_skill_speaking'),
        sa.CheckConstraint('personality_planner     BETWEEN 0 AND 10', name='ck_ielts_personality_planner'),
        sa.CheckConstraint('personality_resourcer   BETWEEN 0 AND 10', name='ck_ielts_personality_resourcer'),
        sa.CheckConstraint('personality_coordinator BETWEEN 0 AND 10', name='ck_ielts_personality_coordinator'),
        sa.CheckConstraint('strength_fluency        BETWEEN 0 AND 10', name='ck_ielts_strength_fluency'),
        sa.CheckConstraint('strength_weekly_hours  >= 0',              name='ck_ielts_strength_weekly_hours'),
        sa.CheckConstraint('strength_target_score  BETWEEN 0 AND 10', name='ck_ielts_strength_target_score'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
    )


def downgrade() -> None:
    op.drop_table('ielts_user_profiles')
