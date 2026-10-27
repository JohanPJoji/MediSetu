import { Warning } from '@phosphor-icons/react';
import { StatusBadge } from '../../components/primitives/Badge';
import styles from './ClinicalHistoryPanel.module.css';

interface ClinicalHistory {
  chief_complaint?: string;
  duration?: string;
  severity?: string;
  character?: string;
  associated_symptoms?: string[];
  red_flags?: string[];
  triage_alert?: boolean;
}

interface ClinicalHistoryPanelProps {
  history: ClinicalHistory;
}

/**
 * ClinicalHistoryPanel — structured display of AI-processed intake.
 * Red flags use StatusBadge (critical, icon+label) — never color alone.
 */
export function ClinicalHistoryPanel({ history }: ClinicalHistoryPanelProps) {
  const hasRedFlags = Array.isArray(history.red_flags) && history.red_flags.length > 0;

  return (
    <div className={styles.panel}>
      <div className={styles.panelHeader}>
        <span>Clinical History</span>
        {history.triage_alert && (
          <StatusBadge severity="critical" label="Triage alert" />
        )}
      </div>

      <div className={styles.panelBody}>
        {hasRedFlags && (
          <div className={styles.redFlagsBox} role="alert">
            <div className={styles.redFlagsHeader}>
              <Warning size={16} aria-hidden="true" />
              <span>Red flags</span>
            </div>
            <ul className={styles.redFlagsList}>
              {(history.red_flags ?? []).map((flag, i) => (
                <li key={i}>{flag}</li>
              ))}
            </ul>
          </div>
        )}

        <dl className={styles.fieldList}>
          {history.chief_complaint && (
            <div className={styles.field}>
              <dt className={styles.fieldLabel}>Chief complaint</dt>
              <dd className={styles.fieldValue}>{history.chief_complaint}</dd>
            </div>
          )}
          {history.duration && (
            <div className={styles.field}>
              <dt className={styles.fieldLabel}>Duration</dt>
              <dd className={styles.fieldValue}>{history.duration}</dd>
            </div>
          )}
          {history.severity && (
            <div className={styles.field}>
              <dt className={styles.fieldLabel}>Severity</dt>
              <dd className={styles.fieldValue}>{history.severity}</dd>
            </div>
          )}
          {history.character && (
            <div className={styles.field}>
              <dt className={styles.fieldLabel}>Character</dt>
              <dd className={styles.fieldValue}>{history.character}</dd>
            </div>
          )}
          {Array.isArray(history.associated_symptoms) && history.associated_symptoms.length > 0 && (
            <div className={styles.field}>
              <dt className={styles.fieldLabel}>Associated symptoms</dt>
              <dd className={styles.fieldValue}>
                {history.associated_symptoms.join(', ')}
              </dd>
            </div>
          )}
        </dl>
      </div>
    </div>
  );
}
