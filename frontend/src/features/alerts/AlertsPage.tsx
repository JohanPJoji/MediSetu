import { useEffect, useState } from 'react';
import { WarningCircle, Check } from '@phosphor-icons/react';
import { api } from '../../lib/api';
import { Button } from '../../components/primitives/Button';
import { StatusBadge } from '../../components/primitives/Badge';
import { EmptyState } from '../../components/primitives/EmptyState';
import { useToast } from '../../components/primitives/Toast';
import styles from './AlertsPage.module.css';

interface Alert {
  id: string;
  patient_id?: string;
  type: string;
  severity: string;
  message: string;
  status: string;
  created_at: string;
}

function sevBadge(s: string) {
  switch (s?.toUpperCase()) {
    case 'HIGH': return 'critical' as const;
    case 'MEDIUM': return 'warning' as const;
    case 'LOW': return 'info' as const;
    default: return 'info' as const;
  }
}

function formatDate(iso: string) {
  try { return new Date(iso).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' }); }
  catch { return iso; }
}

export function AlertsPage() {
  const { toast } = useToast();
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const r = await api.alerts();
      setAlerts(r.data as Alert[]);
    } catch (err) {
      toast({ severity: 'warning', title: 'Could not load alerts', message: err instanceof Error ? err.message : undefined });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleResolve = async (id: string) => {
    // The real API doesn't have a resolve alert endpoint currently, 
    // so we simulate optimistic local state update for the frontend flow as per requirements.
    setAlerts(alerts.map(a => a.id === id ? { ...a, status: 'RESOLVED' } : a));
    toast({ severity: 'success', title: 'Alert resolved' });
  };

  const activeAlerts = alerts.filter(a => a.status?.toUpperCase() !== 'RESOLVED');
  const resolvedAlerts = alerts.filter(a => a.status?.toUpperCase() === 'RESOLVED');

  return (
    <div className={styles.page}>
      <div className={styles.pageHeader}>
        <h1 className={styles.title}>System Alerts</h1>
      </div>

      {loading ? (
        <p className={styles.loadingText}>Loading alerts…</p>
      ) : activeAlerts.length === 0 && resolvedAlerts.length === 0 ? (
        <EmptyState
          icon={<WarningCircle size={40} />}
          title="No alerts"
          description="System alerts will appear here."
        />
      ) : (
        <div className={styles.content}>
          {activeAlerts.length > 0 && (
            <div className={styles.section}>
              <h2 className={styles.sectionTitle}>Active Alerts</h2>
              <div className={styles.list}>
                {activeAlerts.map(a => (
                  <div key={a.id} className={`${styles.card} ${styles['card' + sevBadge(a.severity)]}`}>
                    <div className={styles.cardHeader}>
                      <span className={styles.alertType}>{a.type.replace('_', ' ')}</span>
                      <StatusBadge severity={sevBadge(a.severity)} label={`${a.severity} SEVERITY`} />
                    </div>
                    <p className={styles.message}>{a.message}</p>
                    <div className={styles.metaRow}>
                      <span className={styles.metaDate}>{formatDate(a.created_at)}</span>
                      <Button variant="secondary" size="sm" icon={<Check size={16} />} onClick={() => handleResolve(a.id)}>
                        Resolve
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {resolvedAlerts.length > 0 && (
            <div className={styles.section}>
              <h2 className={styles.sectionTitle}>Resolved</h2>
              <div className={styles.list}>
                {resolvedAlerts.map(a => (
                  <div key={a.id} className={`${styles.card} ${styles.cardResolved}`}>
                    <div className={styles.cardHeader}>
                      <span className={styles.alertType}>{a.type.replace('_', ' ')}</span>
                      <StatusBadge severity="success" label="RESOLVED" />
                    </div>
                    <p className={styles.message}>{a.message}</p>
                    <div className={styles.metaRow}>
                      <span className={styles.metaDate}>{formatDate(a.created_at)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
