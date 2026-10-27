"""add laboratory, billing, inventory batches and medicine alerts

Revision ID: a1b2c3d4e5f6
Revises: 9e2f3a4b5c6d
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "a1b2c3d4e5f6"
down_revision = "9e2f3a4b5c6d"
branch_labels = None
depends_on = None
UUID = postgresql.UUID(as_uuid=True)

def upgrade():
    op.create_table("laboratory_tests",
        sa.Column("id", UUID, primary_key=True), sa.Column("name", sa.String(255), nullable=False),
        sa.Column("code", sa.String(64), nullable=False), sa.Column("department", sa.String(255)),
        sa.Column("price", sa.Numeric(12,2), nullable=False), sa.Column("sample_type", sa.String(100)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_laboratory_tests_name", "laboratory_tests", ["name"]); op.create_index("ix_laboratory_tests_code", "laboratory_tests", ["code"], unique=True)
    op.create_table("lab_orders",
        sa.Column("id", UUID, primary_key=True), sa.Column("patient_id", UUID, nullable=False), sa.Column("doctor_id", UUID, nullable=False),
        sa.Column("consultation_id", UUID), sa.Column("test_id", UUID, nullable=False), sa.Column("status", sa.String(32), nullable=False),
        sa.Column("ordered_at", sa.DateTime(timezone=True), nullable=False), sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["patient_id"],["patients.id"],ondelete="CASCADE"), sa.ForeignKeyConstraint(["doctor_id"],["users.id"],ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["consultation_id"],["consultations.id"],ondelete="SET NULL"), sa.ForeignKeyConstraint(["test_id"],["laboratory_tests.id"],ondelete="RESTRICT"))
    op.create_index("ix_lab_orders_patient_id", "lab_orders", ["patient_id"]); op.create_index("ix_lab_orders_doctor_id", "lab_orders", ["doctor_id"]); op.create_index("ix_lab_orders_consultation_id", "lab_orders", ["consultation_id"])
    op.create_table("lab_results",
        sa.Column("id", UUID, primary_key=True), sa.Column("lab_order_id", UUID, nullable=False), sa.Column("test_id", UUID, nullable=False),
        sa.Column("result_value", sa.Text, nullable=False), sa.Column("reference_range", sa.String(255)), sa.Column("remarks", sa.Text),
        sa.Column("verified_by", UUID), sa.Column("verified_at", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["lab_order_id"],["lab_orders.id"],ondelete="CASCADE"), sa.ForeignKeyConstraint(["test_id"],["laboratory_tests.id"],ondelete="RESTRICT"), sa.ForeignKeyConstraint(["verified_by"],["users.id"],ondelete="SET NULL"), sa.UniqueConstraint("lab_order_id"))
    op.create_index("ix_lab_results_lab_order_id", "lab_results", ["lab_order_id"])
    op.create_table("bills",
        sa.Column("id", UUID, primary_key=True), sa.Column("bill_number", sa.String(32), nullable=False), sa.Column("patient_id", UUID, nullable=False),
        sa.Column("consultation_id", UUID), sa.Column("subtotal", sa.Numeric(12,2), nullable=False), sa.Column("discount", sa.Numeric(12,2), nullable=False),
        sa.Column("tax", sa.Numeric(12,2), nullable=False), sa.Column("total_amount", sa.Numeric(12,2), nullable=False), sa.Column("payment_status", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.ForeignKeyConstraint(["patient_id"],["patients.id"],ondelete="CASCADE"), sa.ForeignKeyConstraint(["consultation_id"],["consultations.id"],ondelete="SET NULL"), sa.UniqueConstraint("bill_number"))
    op.create_index("ix_bills_bill_number", "bills", ["bill_number"], unique=True); op.create_index("ix_bills_patient_id", "bills", ["patient_id"]); op.create_index("ix_bills_consultation_id", "bills", ["consultation_id"])
    op.create_table("bill_items",
        sa.Column("id", UUID, primary_key=True), sa.Column("bill_id", UUID, nullable=False), sa.Column("item_type", sa.String(32), nullable=False),
        sa.Column("item_reference_id", sa.String(64)), sa.Column("description", sa.String(500), nullable=False), sa.Column("quantity", sa.Integer, nullable=False),
        sa.Column("unit_price", sa.Numeric(12,2), nullable=False), sa.Column("total_price", sa.Numeric(12,2), nullable=False), sa.ForeignKeyConstraint(["bill_id"],["bills.id"],ondelete="CASCADE"))
    op.create_index("ix_bill_items_bill_id", "bill_items", ["bill_id"])
    op.create_table("payments",
        sa.Column("id", UUID, primary_key=True), sa.Column("bill_id", UUID, nullable=False), sa.Column("amount", sa.Numeric(12,2), nullable=False),
        sa.Column("payment_method", sa.String(32), nullable=False), sa.Column("transaction_reference", sa.String(255)), sa.Column("payment_status", sa.String(16), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True)), sa.ForeignKeyConstraint(["bill_id"],["bills.id"],ondelete="CASCADE"))
    op.create_index("ix_payments_bill_id", "payments", ["bill_id"])
    op.create_table("inventory_batches",
        sa.Column("id", UUID, primary_key=True), sa.Column("medicine_id", UUID, nullable=False), sa.Column("batch_number", sa.String(100), nullable=False),
        sa.Column("expiry_date", sa.Date, nullable=False), sa.Column("quantity", sa.Integer, nullable=False), sa.Column("reorder_level", sa.Integer, nullable=False),
        sa.Column("location", sa.String(255)), sa.Column("status", sa.String(32), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["medicine_id"],["medicines.id"],ondelete="CASCADE"))
    op.create_index("ix_inventory_batches_medicine_id", "inventory_batches", ["medicine_id"]); op.create_index("ix_inventory_batches_batch_number", "inventory_batches", ["batch_number"])
    op.create_table("medicine_alerts",
        sa.Column("id", UUID, primary_key=True), sa.Column("prescription_id", UUID, nullable=False), sa.Column("medicine_id", UUID, nullable=False), sa.Column("patient_id", UUID, nullable=False),
        sa.Column("doctor_id", UUID, nullable=False), sa.Column("required_quantity", sa.Integer, nullable=False), sa.Column("available_quantity", sa.Integer, nullable=False),
        sa.Column("reason", sa.Text), sa.Column("status", sa.String(32), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["prescription_id"],["prescriptions.id"],ondelete="CASCADE"), sa.ForeignKeyConstraint(["medicine_id"],["medicines.id"],ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["patient_id"],["patients.id"],ondelete="CASCADE"), sa.ForeignKeyConstraint(["doctor_id"],["users.id"],ondelete="RESTRICT"))
    op.create_index("ix_medicine_alerts_prescription_id", "medicine_alerts", ["prescription_id"]); op.create_index("ix_medicine_alerts_patient_id", "medicine_alerts", ["patient_id"]); op.create_index("ix_medicine_alerts_doctor_id", "medicine_alerts", ["doctor_id"])
    op.create_table("alternative_medicines",
        sa.Column("id", UUID, primary_key=True), sa.Column("medicine_id", UUID, nullable=False), sa.Column("alternative_medicine_id", UUID, nullable=False),
        sa.Column("created_by", UUID), sa.Column("status", sa.String(16), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["medicine_id"],["medicines.id"],ondelete="CASCADE"), sa.ForeignKeyConstraint(["alternative_medicine_id"],["medicines.id"],ondelete="CASCADE"), sa.ForeignKeyConstraint(["created_by"],["users.id"],ondelete="SET NULL"))

def downgrade():
    for t in ["alternative_medicines","medicine_alerts","inventory_batches","payments","bill_items","bills","lab_results","lab_orders","laboratory_tests"]: op.drop_table(t)
