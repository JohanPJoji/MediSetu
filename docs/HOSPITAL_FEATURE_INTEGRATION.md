# Hospital Feature Integration

The companion `hospital-backend` project was used as a feature source only.
MediSetu remains the source of truth for identity, RBAC, patients, consultations,
prescriptions, medicines, pharmacy orders, referrals, documents and timeline.

Integrated as UUID-native MediSetu features:

- Laboratory tests/orders/results
- Billing and bill items
- Payments
- Inventory batches
- Inventory transaction ledger and total medicine-stock synchronization
- Medicine shortage alerts
- Alternative medicine mappings

The companion project's integer-primary-key models, duplicate authentication,
patient/doctor/consultation models, and unprotected routes were intentionally not
copied into MediSetu.

API prefixes:

- `/api/laboratory`
- `/api/billing`
- `/api/inventory`
- `/api/alerts`

Migration: `a1b2c3d4e5f6_add_lab_billing_inventory_alerts.py`
