"""add consultations table phase 4 consultation

Revision ID: 5e6c7d8f9a0b
Revises: a823fb84d48f
Create Date: 2026-09-15 18:30:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "5e6c7d8f9a0b"
down_revision = "a823fb84d48f"
branch_labels = None
depends_on = None


def upgrade():
    consultation_status_enum = postgresql.ENUM(
        "CREATED",
        "IN_PROGRESS",
        "AI_PROCESSING",
        "UNDER_REVIEW",
        "APPROVED",
        "COMPLETED",
        "CANCELLED",
        name="consultation_status",
    )
    consultation_status_enum.create(op.get_bind(), checkfirst=True)

    # The enum is created explicitly above; do not let create_table create it again.
    consultation_status_enum = postgresql.ENUM(
        "CREATED", "IN_PROGRESS", "AI_PROCESSING", "UNDER_REVIEW",
        "APPROVED", "COMPLETED", "CANCELLED",
        name="consultation_status", create_type=False,
    )

    op.create_table(
        "consultations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("patient_id", sa.UUID(), nullable=False),
        sa.Column("doctor_id", sa.UUID(), nullable=True),
        sa.Column("status", consultation_status_enum, nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["doctor_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patients.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_consultations_doctor_id"),
        "consultations",
        ["doctor_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_consultations_id"),
        "consultations",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_consultations_patient_id"),
        "consultations",
        ["patient_id"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        op.f("ix_consultations_patient_id"),
        table_name="consultations",
    )
    op.drop_index(
        op.f("ix_consultations_id"),
        table_name="consultations",
    )
    op.drop_index(
        op.f("ix_consultations_doctor_id"),
        table_name="consultations",
    )
    op.drop_table("consultations")

    consultation_status_enum = postgresql.ENUM(
        "CREATED",
        "IN_PROGRESS",
        "AI_PROCESSING",
        "UNDER_REVIEW",
        "APPROVED",
        "COMPLETED",
        "CANCELLED",
        name="consultation_status",
    )
    consultation_status_enum.drop(op.get_bind(), checkfirst=True)