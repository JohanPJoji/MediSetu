import { useEffect, useState } from 'react';
import { Receipt } from '@phosphor-icons/react';
import { api } from '../../lib/api';
import { StatusBadge } from '../../components/primitives/Badge';
import { EmptyState } from '../../components/primitives/EmptyState';
import { useToast } from '../../components/primitives/Toast';
import { useAuth } from '../../app/AuthContext';
import styles from './BillingPage.module.css';

interface Bill {
  id: string;
  total_amount: number;
  status: string;
  created_at?: string;
  items?: Array<{ description: string; amount: number }>;
}

function statusSev(s: string) {
  switch (s?.toUpperCase()) {
    case 'PAID':    return 'success' as const;
    case 'PENDING': return 'warning' as const;
    case 'OVERDUE': return 'critical' as const;
    default:        return 'pending' as const;
  }
}

function formatCurrency(n: number) {
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 2 }).format(n);
}

function formatDate(iso?: string) {
  if (!iso) return '—';
  try { return new Date(iso).toLocaleDateString([], { dateStyle: 'medium' }); }
  catch { return iso; }
}

export function BillingPage() {
  const { user } = useAuth();
  const { toast } = useToast();
  const [bills, setBills]     = useState<Bill[]>([]);
  const [loading, setLoading] = useState(true);
  const isPatient = user?.role === 'PATIENT';

  useEffect(() => {
    api.bills()
      .then((r) => setBills(r.data as Bill[]))
      .catch((err) => toast({ severity: 'warning', title: 'Could not load bills', message: err instanceof Error ? err.message : undefined }))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className={styles.page}>
      <div className={styles.pageHeader}>
        <h1 className={styles.title}>Billing</h1>
      </div>

      {loading ? (
        <p className={styles.loadingText}>Loading bills…</p>
      ) : bills.length === 0 ? (
        <EmptyState
          icon={<Receipt size={40} />}
          title="No bills"
          description={isPatient ? 'Invoices from your consultations will appear here.' : 'No billing records found.'}
        />
      ) : (
        <div className={styles.billList}>
          {bills.map((bill) => (
            <div key={bill.id} className={styles.billCard}>
              <div className={styles.billHeader}>
                <span className={styles.billId}>Invoice {bill.id.slice(0, 8)}…</span>
                <StatusBadge severity={statusSev(bill.status)} label={bill.status ?? 'PENDING'} />
              </div>
              <div className={styles.billMeta}>
                <span className={styles.billDate}>{formatDate(bill.created_at)}</span>
                <span className={styles.billTotal}>{formatCurrency(bill.total_amount ?? 0)}</span>
              </div>
              {Array.isArray(bill.items) && bill.items.length > 0 && (
                <ul className={styles.lineItems}>
                  {bill.items.map((item, i) => (
                    <li key={i} className={styles.lineItem}>
                      <span>{item.description}</span>
                      <span className={styles.lineAmt}>{formatCurrency(item.amount)}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
