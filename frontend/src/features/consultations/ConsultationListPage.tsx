import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Stethoscope } from '@phosphor-icons/react';
import { api } from '../../lib/api';
import { useAuth } from '../../app/AuthContext';
import { Button } from '../../components/primitives/Button';
import { Table } from '../../components/primitives/Table';
import { StatusBadge } from '../../components/primitives/Badge';
import { EmptyState } from '../../components/primitives/EmptyState';
import { Input } from '../../components/primitives/Input';
import { Modal } from '../../components/primitives/Modal';
import { useToast } from '../../components/primitives/Toast';
import styles from './ConsultationListPage.module.css';

interface Consultation {
  id: string;
  status: string;
  created_at?: string;
  patient_id?: string;
}

type ConsultationStatus = 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED';

function statusSeverity(status: string) {
  switch (status?.toUpperCase()) {
    case 'IN_PROGRESS': return 'warning' as const;
    case 'COMPLETED':   return 'success' as const;
    case 'CANCELLED':   return 'info' as const;
    default:            return 'pending' as const;
  }
}

function formatDate(iso?: string) {
  if (!iso) return '—';
  try { return new Date(iso).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' }); }
  catch { return iso; }
}

export function ConsultationListPage() {
  const { user } = useAuth();
  const navigate  = useNavigate();
  const { toast } = useToast();

  const [consultations, setConsultations] = useState<Consultation[]>([]);
  const [loading, setLoading]  = useState(true);
  const [patientId, setPatientId] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [creating, setCreating]   = useState(false);
  const [profileMissing, setProfileMissing] = useState(false);
  const [ownPatientId, setOwnPatientId]     = useState('');

  const isPatient = user?.role === 'PATIENT';

  const load = async () => {
    setLoading(true);
    try {
      const r = await api.consultations();
      setConsultations(r.data as Consultation[]);
    } catch (err) {
      toast({ severity: 'warning', title: 'Could not load consultations', message: err instanceof Error ? err.message : undefined });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    if (isPatient) {
      api.patientMe()
        .then((r) => { setOwnPatientId(r.data.id); setProfileMissing(false); })
        .catch(() => setProfileMissing(true));
    }
  }, []);

  // Redirect patient to onboarding if no profile
  useEffect(() => {
    if (isPatient && profileMissing && !loading) {
      navigate('/onboarding', { replace: true });
    }
  }, [isPatient, profileMissing, loading]);

  const handleCreate = async () => {
    setCreating(true);
    try {
      const pid = isPatient ? ownPatientId : patientId.trim();
      await api.createConsultation(pid);
      toast({ severity: 'success', title: 'Consultation created' });
      setShowModal(false);
      setPatientId('');
      await load();
    } catch (err) {
      toast({ severity: 'critical', title: 'Failed to create consultation', message: err instanceof Error ? err.message : undefined, persistent: true });
    } finally {
      setCreating(false);
    }
  };

  const columns = [
    {
      key: 'id',
      header: 'ID',
      mono: true,
      sortable: false,
      render: (row: Consultation) => row.id.slice(0, 8) + '…',
    },
    {
      key: 'status',
      header: 'Status',
      sortable: true,
      render: (row: Consultation) => (
        <StatusBadge
          severity={statusSeverity(row.status)}
          label={row.status ?? 'PENDING'}
        />
      ),
    },
    {
      key: 'created_at',
      header: 'Created',
      sortable: true,
      render: (row: Consultation) => <span className="mono">{formatDate(row.created_at)}</span>,
    },
  ];

  const canCreate = ['PATIENT', 'DOCTOR', 'NURSE', 'ADMIN'].includes(user?.role ?? '');

  return (
    <div className={styles.page}>
      <div className={styles.pageHeader}>
        <h1 className={styles.title}>Consultations</h1>
        {canCreate && (
          <Button
            variant="primary"
            icon={<Plus size={16} />}
            onClick={() => isPatient ? handleCreate() : setShowModal(true)}
            loading={creating && isPatient}
          >
            {isPatient ? 'Start consultation' : 'New consultation'}
          </Button>
        )}
      </div>

      {loading ? (
        <p className={styles.loadingText}>Loading consultations…</p>
      ) : consultations.length === 0 ? (
        <EmptyState
          icon={<Stethoscope size={40} />}
          title="No consultations yet"
          description={isPatient
            ? 'Start a consultation to speak with an AI assistant — a doctor will review everything.'
            : 'No consultations have been created yet.'}
          action={canCreate ? (
            <Button variant="primary" onClick={() => isPatient ? handleCreate() : setShowModal(true)}>
              {isPatient ? 'Start consultation' : 'New consultation'}
            </Button>
          ) : undefined}
        />
      ) : (
        <Table
          columns={columns as any}
          rows={consultations as any}
          rowKey="id"
          caption="All consultations"
          emptyMessage="No consultations found."
        />
      )}

      {/* Click row → detail */}
      {consultations.length > 0 && (
        <div className={styles.clickHint}>
          Click any row above to open a consultation — or use the table below.
        </div>
      )}
      {/* Clickable rows via separate list for accessible navigation */}
      {consultations.length > 0 && (
        <ul className={styles.consultationList} aria-label="Consultations">
          {consultations.map((c) => (
            <li key={c.id}>
              <button
                type="button"
                className={styles.consultationRow}
                onClick={() => navigate(`/consultations/${c.id}`)}
              >
                <span className={styles.consultationId}>{c.id.slice(0, 8)}…</span>
                <StatusBadge severity={statusSeverity(c.status)} label={c.status ?? 'PENDING'} />
                <span className={styles.consultationDate}>{formatDate(c.created_at)}</span>
              </button>
            </li>
          ))}
        </ul>
      )}

      {/* Create modal (clinical roles) */}
      <Modal
        open={showModal}
        onClose={() => setShowModal(false)}
        title="New consultation"
        footer={
          <>
            <Button variant="ghost" onClick={() => setShowModal(false)}>Cancel</Button>
            <Button variant="primary" loading={creating} onClick={handleCreate} disabled={!patientId.trim()}>
              Create
            </Button>
          </>
        }
      >
        <Input
          id="patient-uuid"
          label="Patient ID (UUID)"
          value={patientId}
          onChange={(e) => setPatientId(e.target.value)}
          placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
          hint="Enter the patient's system UUID."
          required
        />
      </Modal>
    </div>
  );
}
