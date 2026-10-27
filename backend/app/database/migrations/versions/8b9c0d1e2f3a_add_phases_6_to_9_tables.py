"""add phases 6 to 9 tables

Revision ID: 8b9c0d1e2f3a
Revises: 7a8b9c0d1e2f
Create Date: 2026-09-15 19:35:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '8b9c0d1e2f3a'
down_revision = '7a8b9c0d1e2f'
branch_labels = None
depends_on = None

def upgrade():
    # 1. Diagnoses
    op.create_table(
        'diagnoses',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('consultation_id', sa.UUID(), nullable=False),
        sa.Column('doctor_id', sa.UUID(), nullable=True),
        sa.Column('condition', sa.String(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['consultation_id'], ['consultations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['doctor_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_diagnoses_consultation_id'), 'diagnoses', ['consultation_id'], unique=False)
    op.create_index(op.f('ix_diagnoses_id'), 'diagnoses', ['id'], unique=False)

    # 2. Medicines
    op.create_table(
        'medicines',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('current_stock', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('reserved_stock', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_medicines_id'), 'medicines', ['id'], unique=False)

    # 3. Prescriptions
    prescription_status_enum = postgresql.ENUM('DRAFT', 'CONFIRMED', 'PREPARING', 'READY', 'DISPENSED', 'CANCELLED', name='prescription_status')
    prescription_status_enum.create(op.get_bind(), checkfirst=True)
    prescription_status_enum = postgresql.ENUM('DRAFT', 'CONFIRMED', 'PREPARING', 'READY', 'DISPENSED', 'CANCELLED', name='prescription_status', create_type=False)

    op.create_table(
        'prescriptions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('consultation_id', sa.UUID(), nullable=False),
        sa.Column('doctor_id', sa.UUID(), nullable=True),
        sa.Column('patient_id', sa.UUID(), nullable=False),
        sa.Column('status', prescription_status_enum, nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['consultation_id'], ['consultations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['doctor_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_prescriptions_consultation_id'), 'prescriptions', ['consultation_id'], unique=False)
    op.create_index(op.f('ix_prescriptions_id'), 'prescriptions', ['id'], unique=False)

    # 4. Prescription Items
    op.create_table(
        'prescription_items',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('prescription_id', sa.UUID(), nullable=False),
        sa.Column('medicine_id', sa.UUID(), nullable=False),
        sa.Column('dosage', sa.String(), nullable=False),
        sa.Column('frequency', sa.String(), nullable=False),
        sa.Column('duration', sa.String(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['medicine_id'], ['medicines.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['prescription_id'], ['prescriptions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_prescription_items_id'), 'prescription_items', ['id'], unique=False)
    op.create_index(op.f('ix_prescription_items_prescription_id'), 'prescription_items', ['prescription_id'], unique=False)

    # 5. Referrals
    referral_status_enum = postgresql.ENUM('PENDING', 'ACCEPTED', 'REJECTED', 'COMPLETED', name='referral_status')
    referral_status_enum.create(op.get_bind(), checkfirst=True)
    referral_status_enum = postgresql.ENUM('PENDING', 'ACCEPTED', 'REJECTED', 'COMPLETED', name='referral_status', create_type=False)

    op.create_table(
        'referrals',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('consultation_id', sa.UUID(), nullable=False),
        sa.Column('patient_id', sa.UUID(), nullable=False),
        sa.Column('referring_doctor_id', sa.UUID(), nullable=True),
        sa.Column('referred_doctor_id', sa.UUID(), nullable=True),
        sa.Column('status', referral_status_enum, nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['consultation_id'], ['consultations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['referred_doctor_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['referring_doctor_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_referrals_consultation_id'), 'referrals', ['consultation_id'], unique=False)
    op.create_index(op.f('ix_referrals_id'), 'referrals', ['id'], unique=False)

    # 6. Documents
    op.create_table(
        'documents',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('patient_id', sa.UUID(), nullable=False),
        sa.Column('consultation_id', sa.UUID(), nullable=True),
        sa.Column('file_name', sa.String(), nullable=False),
        sa.Column('file_type', sa.String(), nullable=False),
        sa.Column('file_url', sa.String(), nullable=False),
        sa.Column('extracted_text', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['consultation_id'], ['consultations.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_documents_consultation_id'), 'documents', ['consultation_id'], unique=False)
    op.create_index(op.f('ix_documents_id'), 'documents', ['id'], unique=False)
    op.create_index(op.f('ix_documents_patient_id'), 'documents', ['patient_id'], unique=False)


def downgrade():
    op.drop_table('documents')
    op.drop_table('referrals')
    op.drop_table('prescription_items')
    op.drop_table('prescriptions')
    op.drop_table('medicines')
    op.drop_table('diagnoses')
    
    referral_status_enum = postgresql.ENUM('PENDING', 'ACCEPTED', 'REJECTED', 'COMPLETED', name='referral_status')
    referral_status_enum.drop(op.get_bind(), checkfirst=True)
    prescription_status_enum = postgresql.ENUM('DRAFT', 'CONFIRMED', 'PREPARING', 'READY', 'DISPENSED', 'CANCELLED', name='prescription_status')
    prescription_status_enum.drop(op.get_bind(), checkfirst=True)
