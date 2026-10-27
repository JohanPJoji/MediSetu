import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft } from '@phosphor-icons/react';
import { api } from '../../lib/api';
import { useAuth } from '../../app/AuthContext';
import { Button } from '../../components/primitives/Button';
import { StatusBadge } from '../../components/primitives/Badge';
import { useToast } from '../../components/primitives/Toast';
import { VoiceConsultation } from './VoiceConsultation';
import { SummaryPanel } from './SummaryPanel';
import { MedicineSuggestions } from './MedicineSuggestions';
import { ClinicalHistoryPanel } from './ClinicalHistoryPanel';
import styles from './ConsultationDetailPage.module.css';

interface ConsultationDetail {
  id: string;
  status: string;
  patient_id?: string;
  created_at?: string;
  history?: Record<string, unknown>;
}

function statusSeverity(status: string) {
  switch (status?.toUpperCase()) {
    case 'IN_PROGRESS': return 'warning' as const;
    case 'COMPLETED':   return 'success' as const;
    case 'CANCELLED':   return 'info' as const;
    default:            return 'pending' as const;
  }
}

export function ConsultationDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();

  const [consultation, setConsultation] = useState<ConsultationDetail | null>(null);
  const [loading, setLoading] = useState(true);

  const isPatient  = user?.role === 'PATIENT';
  const isDoctor   = user?.role === 'DOCTOR';
  const isClinical = ['DOCTOR', 'NURSE', 'ADMIN'].includes(user?.role ?? '');

  const load = async () => {
    if (!id) return;
    setLoading(true);
    try {
      const r = await api.consultation(id);
      setConsultation(r.data as ConsultationDetail);
    } catch (err) {
      toast({ severity: 'critical', title: 'Could not load consultation', message: err instanceof Error ? err.message : undefined, persistent: true });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [id]);

  const handleComplete = async () => {
    if (!id) return;
    try {
      await api.completeConsultation(id);
      toast({ severity: 'success', title: 'Consultation completed' });
      await load();
    } catch (err) {
      toast({ severity: 'critical', title: 'Failed to complete consultation', message: err instanceof Error ? err.message : undefined, persistent: true });
    }
  };

  const handleSummary = async () => {
    if (!id) return null;
    const r = await api.summary(id);
    return r.data as { summary?: string; key_points?: string[] };
  };

  const handleMedicines = async () => {
    if (!id) return [];
    const r = await api.medicineSuggestions(id);
    return Array.isArray(r.data) ? r.data : [];
  };

  if (loading) {
    return (
      <div className={styles.page}>
        <p className={styles.loading}>Loading consultation…</p>
      </div>
    );
  }

  if (!consultation) {
    return (
      <div className={styles.page}>
        <p className={styles.loading}>Consultation not found.</p>
        <Button variant="ghost" icon={<ArrowLeft size={16} />} onClick={() => navigate('/consultations')}>
          Back to consultations
        </Button>
      </div>
    );
  }

  const isPending    = consultation.status?.toUpperCase() === 'PENDING' || consultation.status?.toUpperCase() === 'CREATED';
  const isInProgress = consultation.status?.toUpperCase() === 'IN_PROGRESS';
  const isCompleted  = consultation.status?.toUpperCase() === 'COMPLETED';

  const canVoice      = isPatient && (isPending || isInProgress);
  const canComplete   = isClinical && !isCompleted;
  const canSummary    = isClinical;
  const canMedicines  = isDoctor;

  return (
    <div className={styles.page}>
      {/* Header */}
      <div className={styles.pageHeader}>
        <Button
          variant="ghost"
          size="sm"
          icon={<ArrowLeft size={16} />}
          onClick={() => navigate('/consultations')}
        >
          Consultations
        </Button>
        <div className={styles.headerRight}>
          <span className={styles.idLabel}>{consultation.id.slice(0, 8)}…</span>
          <StatusBadge severity={statusSeverity(consultation.status)} label={consultation.status ?? 'PENDING'} />
          {canComplete && (
            <Button variant="secondary" size="sm" onClick={handleComplete}>
              Mark completed
            </Button>
          )}
        </div>
      </div>

      {/* Layout: patient single-column, clinical two-pane */}
      <div className={[styles.layout, isClinical ? styles.clinicalLayout : ''].join(' ')}>
        {/* ─── Left pane ─── */}
        <div className={styles.leftPane}>
          {/* Patient: voice consultation */}
          {canVoice && (
            <VoiceConsultation consultationId={consultation.id} onUpdated={load} />
          )}

          {/* Completed patient view: show history */}
          {isPatient && isCompleted && consultation.history && (
            <ClinicalHistoryPanel history={consultation.history as any} />
          )}

          {/* Clinical: clinical history + transcript */}
          {isClinical && consultation.history && (
            <ClinicalHistoryPanel history={consultation.history as any} />
          )}

          {/* Clinical: transcript is in SummaryPanel section for compact layout */}
        </div>

        {/* ─── Right pane (clinical only) ─── */}
        {isClinical && (
          <div className={styles.rightPane}>
            {canSummary && (
              <SummaryPanel
                consultationId={consultation.id}
                onGenerate={handleSummary}
                canGenerate={canSummary}
              />
            )}
            {canMedicines && (
              <MedicineSuggestions
                consultationId={consultation.id}
                onFetch={handleMedicines}
                canFetch={canMedicines}
              />
            )}
          </div>
        )}
      </div>
    </div>
  );
}
