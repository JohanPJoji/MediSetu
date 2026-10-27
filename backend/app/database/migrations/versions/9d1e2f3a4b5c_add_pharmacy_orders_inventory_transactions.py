"""add pharmacy orders and inventory transactions

Revision ID: 9d1e2f3a4b5c
Revises: 9c0d1e2f3a4b
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "9d1e2f3a4b5c"
down_revision = "9c0d1e2f3a4b"
branch_labels = None
depends_on = None


def upgrade():
    order_status = postgresql.ENUM(
        "PENDING", "RESERVED", "PREPARING", "READY_FOR_PICKUP",
        "DISPENSED", "CANCELLED", "EXPIRED",
        name="pharmacy_order_status",
    )
    order_status.create(op.get_bind(), checkfirst=True)
    order_status = postgresql.ENUM(
        "PENDING", "RESERVED", "PREPARING", "READY_FOR_PICKUP",
        "DISPENSED", "CANCELLED", "EXPIRED",
        name="pharmacy_order_status", create_type=False,
    )

    transaction_type = postgresql.ENUM(
        "STOCK_ADDED", "STOCK_RESERVED", "STOCK_RELEASED",
        "STOCK_DISPENSED", "STOCK_ADJUSTED",
        name="inventory_transaction_type",
    )
    transaction_type.create(op.get_bind(), checkfirst=True)
    transaction_type = postgresql.ENUM(
        "STOCK_ADDED", "STOCK_RESERVED", "STOCK_RELEASED",
        "STOCK_DISPENSED", "STOCK_ADJUSTED",
        name="inventory_transaction_type", create_type=False,
    )

    op.create_table(
        "pharmacy_orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("prescription_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", order_status, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["prescription_id"], ["prescriptions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("prescription_id"),
    )
    op.create_index("ix_pharmacy_orders_prescription_id", "pharmacy_orders", ["prescription_id"], unique=True)
    op.create_index("ix_pharmacy_orders_patient_id", "pharmacy_orders", ["patient_id"], unique=False)

    op.create_table(
        "inventory_transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("medicine_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("prescription_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("transaction_type", transaction_type, nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["medicine_id"], ["medicines.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["prescription_id"], ["prescriptions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["order_id"], ["pharmacy_orders.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_inventory_transactions_medicine_id", "inventory_transactions", ["medicine_id"], unique=False)
    op.create_index("ix_inventory_transactions_prescription_id", "inventory_transactions", ["prescription_id"], unique=False)
    op.create_index("ix_inventory_transactions_order_id", "inventory_transactions", ["order_id"], unique=False)


def downgrade():
    op.drop_index("ix_inventory_transactions_order_id", table_name="inventory_transactions")
    op.drop_index("ix_inventory_transactions_prescription_id", table_name="inventory_transactions")
    op.drop_index("ix_inventory_transactions_medicine_id", table_name="inventory_transactions")
    op.drop_table("inventory_transactions")
    op.drop_index("ix_pharmacy_orders_patient_id", table_name="pharmacy_orders")
    op.drop_index("ix_pharmacy_orders_prescription_id", table_name="pharmacy_orders")
    op.drop_table("pharmacy_orders")
    postgresql.ENUM(name="inventory_transaction_type").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="pharmacy_order_status").drop(op.get_bind(), checkfirst=True)
