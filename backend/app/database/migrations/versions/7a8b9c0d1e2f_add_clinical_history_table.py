"""add clinical history table phase 5

Revision ID: 7a8b9c0d1e2f
Revises: 6f7d8e9f0a1b
Create Date: 2026-09-15 19:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '7a8b9c0d1e2f'
down_revision = '6f7d8e9f0a1b'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'clinical_histories',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('consultation_id', sa.UUID(), nullable=False),
        sa.Column('chief_complaint', sa.Text(), nullable=True),
        sa.Column('history_present_illness', sa.Text(), nullable=True),
        sa.Column('onset', sa.String(), nullable=True),
        sa.Column('duration', sa.String(), nullable=True),
        sa.Column('location', sa.String(), nullable=True),
        sa.Column('character', sa.String(), nullable=True),
        sa.Column('severity', sa.String(), nullable=True),
        sa.Column('timing', sa.String(), nullable=True),
        sa.Column('aggravating_factors', sa.String(), nullable=True),
        sa.Column('relieving_factors', sa.String(), nullable=True),
        sa.Column('associated_symptoms', sa.String(), nullable=True),
        sa.Column('past_medical_history', sa.Text(), nullable=True),
        sa.Column('past_surgical_history', sa.Text(), nullable=True),
        sa.Column('medication_history', sa.Text(), nullable=True),
        sa.Column('allergies', sa.Text(), nullable=True),
        sa.Column('family_history', sa.Text(), nullable=True),
        sa.Column('red_flags', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['consultation_id'], ['consultations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_clinical_histories_consultation_id'), 'clinical_histories', ['consultation_id'], unique=True)
    op.create_index(op.f('ix_clinical_histories_id'), 'clinical_histories', ['id'], unique=False)

def downgrade():
    op.drop_index(op.f('ix_clinical_histories_id'), table_name='clinical_histories')
    op.drop_index(op.f('ix_clinical_histories_consultation_id'), table_name='clinical_histories')
    op.drop_table('clinical_histories')
