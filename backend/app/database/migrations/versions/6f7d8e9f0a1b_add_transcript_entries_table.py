"""add transcript entries table

Revision ID: 6f7d8e9f0a1b
Revises: 5e6c7d8f9a0b
Create Date: 2026-09-15 19:25:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "6f7d8e9f0a1b"
down_revision = "5e6c7d8f9a0b"
branch_labels = None
depends_on = None


def upgrade():
    transcript_role_enum = postgresql.ENUM(
        "PATIENT",
        "SYSTEM",
        name="transcript_role",
    )
    transcript_role_enum.create(op.get_bind(), checkfirst=True)

    # The enum is created explicitly above; do not let create_table create it again.
    transcript_role_enum = postgresql.ENUM(
        "PATIENT", "SYSTEM", name="transcript_role", create_type=False
    )

    op.create_table(
        "transcript_entries",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("consultation_id", sa.UUID(), nullable=False),
        sa.Column("role", transcript_role_enum, nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("language", sa.String(), nullable=False, server_default="en"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["consultation_id"],
            ["consultations.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_transcript_entries_consultation_id"),
        "transcript_entries",
        ["consultation_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_transcript_entries_id"),
        "transcript_entries",
        ["id"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        op.f("ix_transcript_entries_id"),
        table_name="transcript_entries",
    )
    op.drop_index(
        op.f("ix_transcript_entries_consultation_id"),
        table_name="transcript_entries",
    )
    op.drop_table("transcript_entries")

    transcript_role_enum = postgresql.ENUM(
        "PATIENT",
        "SYSTEM",
        name="transcript_role",
    )
    transcript_role_enum.drop(op.get_bind(), checkfirst=True)