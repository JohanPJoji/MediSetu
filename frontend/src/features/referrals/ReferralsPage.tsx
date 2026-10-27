import { useEffect, useState } from 'react';
import { ArrowsClockwise, Plus } from '@phosphor-icons/react';
import { api } from '../../lib/api';
import { useAuth } from '../../app/AuthContext';
import { StatusBadge } from '../../components/primitives/Badge';
import { EmptyState } from '../../components/primitives/EmptyState';
import { Button } from '../../components/primitives/Button';
import { Modal } from '../../components/primitives/Modal';
import { Input } from '../../components/primitives/Input';
import { Select } from '../../components/primitives/Select';
import { useToast } from '../../components/primitives/Toast';
import styles from './ReferralsPage.module.css';

interface Referral {
  id: string;
  consultation_id: string;
  referred_to_specialty: string;
  reason: string;
  priority: string;
  status: string;
  created_at: string;
}

const SPECIALTIES = [
  { value: 'CARDIOLOGY', label: 'Cardiology' },
  { value: 'DERMATOLOGY', label: 'Dermatology' },
  { value: 'ENDOCRINOLOGY', label: 'Endocrinology' },
  { value: 'NEUROLOGY', label: 'Neurology' },
  { value: 'ONCOLOGY', label: 'Oncology' },
  { value: 'PEDIATRICS', label: 'Pediatrics' },
  { value: 'PSYCHIATRY', label: 'Psychiatry' },
  { value: 'GENERAL_SURGERY', label: 'General Surgery' },
  { value: 'OTHER', label: 'Other (specify in reason)' },
];

function formatSev(s: string) {
  switch(s?.toUpperCase()) {
    case 'HIGH':
    case 'URGENT':
    case 'COMPLETED': return 'critical' as const; // for priority
    case 'PENDING': return 'warning' as const;
    default: return 'info' as const;
  }
}
function statusSev(s: string) {
  switch (s?.toUpperCase()) {
    case 'COMPLETED': return 'success' as const;
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

export function ReferralsPage() {
  const { user } = useAuth();
  const { toast } = useToast();
  const [referrals, setReferrals] = useState<Referral[]>([]);
  const [loading, setLoading]     = useState(true);

  // Creation modal state
  const [showModal, setShowModal] = useState(false);
  const [creating, setCreating]   = useState(false);
  const [consultId, setConsultId] = useState('');
  const [specialty, setSpecialty] = useState('CARDIOLOGY');
  const [reason, setReason]       = useState('');
  const [priority, setPriority]   = useState('ROUTINE');

  const isPatient = user?.role === 'PATIENT';
  const canCreate = ['DOCTOR', 'NURSE', 'ADMIN'].includes(user?.role ?? '');

  const load = async () => {
    setLoading(true);
    try {
      const r = await api.referrals();
      setReferrals(r.data as Referral[]);
    } catch (err) {
      toast({ severity: 'warning', title: 'Could not load referrals', message: err instanceof Error ? err.message : undefined });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleCreate = async () => {
    setCreating(true);
    try {
      await api.createReferral(consultId.trim(), specialty, reason.trim(), priority as 'ROUTINE'|'URGENT');
      toast({ severity: 'success', title: 'Referral created' });
      setShowModal(false);
      setConsultId('');
      setSpecialty('CARDIOLOGY');
      setReason('');
      setPriority('ROUTINE');
      await load();
    } catch (err) {
      toast({ severity: 'critical', title: 'Failed to create referral', message: err instanceof Error ? err.message : undefined, persistent: true });
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className={styles.page}>
      <div className={styles.pageHeader}>
        <h1 className={styles.title}>Referrals</h1>
        {canCreate && (
          <Button variant="primary" icon={<Plus size={16} />} onClick={() => setShowModal(true)}>
            New referral
          </Button>
        )}
      </div>

      {loading ? (
        <p className={styles.loadingText}>Loading referrals…</p>
      ) : referrals.length === 0 ? (
        <EmptyState
          icon={<ArrowsClockwise size={40} />}
          title="No referrals"
          description={isPatient ? 'If your doctor refers you to a specialist, it will appear here.' : 'No referrals found.'}
        />
      ) : (
        <div className={styles.grid}>
          {referrals.map((r) => (
            <div key={r.id} className={styles.card}>
              <div className={styles.cardHeader}>
                <h3 className={styles.specialty}>{r.referred_to_specialty.replace('_', ' ')}</h3>
                <StatusBadge severity={statusSev(r.status)} label={r.status ?? 'PENDING'} />
              </div>
              <div className={styles.metaRow}>
                <span className={styles.metaId}>{r.id.slice(0, 8)}…</span>
                <span className={styles.metaDate}>{formatDate(r.created_at)}</span>
              </div>
              <div className={styles.reasonBox}>
                <span className={styles.label}>Reason</span>
                <p className={styles.value}>{r.reason}</p>
              </div>
              <div className={styles.footer}>
                <StatusBadge severity={formatSev(r.priority)} label={`${r.priority} PRIORITY`} />
              </div>
            </div>
          ))}
        </div>
      )}

      <Modal
        open={showModal}
        onClose={() => setShowModal(false)}
        title="Create referral"
        footer={
          <>
            <Button variant="ghost" onClick={() => setShowModal(false)}>Cancel</Button>
            <Button
              variant="primary"
              loading={creating}
              onClick={handleCreate}
              disabled={!consultId.trim() || !reason.trim()}
            >
              Create referral
            </Button>
          </>
        }
      >
        <div className={styles.modalBody}>
          <Input
            id="ref-consult-id"
            label="Consultation ID (UUID)"
            value={consultId}
            onChange={(e) => setConsultId(e.target.value)}
            required
          />
          <Select
            id="ref-specialty"
            label="Specialty"
            options={SPECIALTIES}
            value={specialty}
            onChange={(e) => setSpecialty(e.target.value)}
            required
          />
          <Select
            id="ref-priority"
            label="Priority"
            options={[{ value: 'ROUTINE', label: 'Routine' }, { value: 'URGENT', label: 'Urgent' }]}
            value={priority}
            onChange={(e) => setPriority(e.target.value)}
            required
          />
          <Input
            id="ref-reason"
            label="Reason for referral"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            required
          />
        </div>
      </Modal>
    </div>
  );
}
