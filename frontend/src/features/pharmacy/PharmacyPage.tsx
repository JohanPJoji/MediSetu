import { useEffect, useState } from 'react';
import { Pill } from '@phosphor-icons/react';
import { api } from '../../lib/api';
import { Button } from '../../components/primitives/Button';
import { StatusBadge } from '../../components/primitives/Badge';
import { EmptyState } from '../../components/primitives/EmptyState';
import { useToast } from '../../components/primitives/Toast';
import styles from './PharmacyPage.module.css';

interface Prescription {
  id: string;
  consultation_id: string;
  medicine_name: string;
  dosage: string;
  frequency: string;
  duration: string;
  status: string;
  created_at: string;
}

function statusSev(s: string) {
  switch (s?.toUpperCase()) {
    case 'DISPENSED': return 'success' as const;
    case 'PENDING':   return 'warning' as const;
    case 'CANCELLED': return 'critical' as const;
    default:          return 'pending' as const;
  }
}

function formatDate(iso?: string) {
  if (!iso) return '—';
  try { return new Date(iso).toLocaleDateString([], { dateStyle: 'medium' }); }
  catch { return iso; }
}

export function PharmacyPage() {
  const { toast } = useToast();
  const [prescriptions, setPrescriptions] = useState<Prescription[]>([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const r = await api.prescriptions();
      setPrescriptions(r.data as Prescription[]);
    } catch (err) {
      toast({ severity: 'warning', title: 'Could not load prescriptions', message: err instanceof Error ? err.message : undefined });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleDispense = async (id: string) => {
    try {
      await api.dispensePrescription(id);
      toast({ severity: 'success', title: 'Prescription marked as dispensed' });
      await load();
    } catch (err) {
      toast({ severity: 'critical', title: 'Failed to dispense', message: err instanceof Error ? err.message : undefined, persistent: true });
    }
  };

  return (
    <div className={styles.page}>
      <div className={styles.pageHeader}>
        <h1 className={styles.title}>Pharmacy</h1>
      </div>

      {loading ? (
        <p className={styles.loadingText}>Loading prescriptions…</p>
      ) : prescriptions.length === 0 ? (
        <EmptyState
          icon={<Pill size={40} />}
          title="No prescriptions"
          description="Confirmed prescriptions from doctor consultations will appear here."
        />
      ) : (
        <div className={styles.grid}>
          {prescriptions.map((p) => (
            <div key={p.id} className={styles.card}>
              <div className={styles.cardHeader}>
                <h3 className={styles.medicineName}>{p.medicine_name}</h3>
                <StatusBadge severity={statusSev(p.status)} label={p.status ?? 'PENDING'} />
              </div>
              <div className={styles.metaRow}>
                <span className={styles.metaId}>{p.id.slice(0, 8)}…</span>
                <span className={styles.metaDate}>{formatDate(p.created_at)}</span>
              </div>
              <div className={styles.details}>
                <div className={styles.detailItem}>
                  <span className={styles.detailLabel}>Dosage</span>
                  <span className={styles.detailValue}>{p.dosage}</span>
                </div>
                <div className={styles.detailItem}>
                  <span className={styles.detailLabel}>Frequency</span>
                  <span className={styles.detailValue}>{p.frequency}</span>
                </div>
                <div className={styles.detailItem}>
                  <span className={styles.detailLabel}>Duration</span>
                  <span className={styles.detailValue}>{p.duration}</span>
                </div>
              </div>
              <div className={styles.actions}>
                {p.status?.toUpperCase() !== 'DISPENSED' && (
                  <Button variant="primary" size="sm" onClick={() => handleDispense(p.id)}>
                    Mark dispensed
                  </Button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
