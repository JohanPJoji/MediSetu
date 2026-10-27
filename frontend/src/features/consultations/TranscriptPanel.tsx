import styles from './TranscriptPanel.module.css';

export interface TranscriptTurn {
  id: string;
  role: 'PATIENT' | 'SYSTEM' | 'DOCTOR' | 'AI';
  content: string;
  created_at: string;
}

interface TranscriptPanelProps {
  turns: TranscriptTurn[];
  loading?: boolean;
}

const ROLE_LABELS: Record<string, string> = {
  PATIENT: 'Patient',
  SYSTEM:  'AI Assistant',
  AI:      'AI Assistant',
  DOCTOR:  'Doctor',
  NURSE:   'Nurse',
};

function formatTime(iso: string): string {
  try {
    return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
  } catch {
    return iso;
  }
}

/**
 * TranscriptPanel — design.md § Components/Transcript
 * Structured record: speaker label (label type) + timestamp (Plex Mono) + plain text.
 * NOT chat bubbles. This is a clinical record, not a messaging app.
 * Supports multilingual text natively via Noto Sans fallback in font stack.
 */
export function TranscriptPanel({ turns, loading }: TranscriptPanelProps) {
  if (loading) {
    return (
      <div className={styles.panel}>
        <div className={styles.header}>Transcript</div>
        <div className={styles.empty}>Loading transcript…</div>
      </div>
    );
  }

  return (
    <div className={styles.panel}>
      <div className={styles.header}>Transcript</div>
      {turns.length === 0 ? (
        <div className={styles.empty}>
          No transcript yet. The conversation will appear here once you begin.
        </div>
      ) : (
        <ol className={styles.list} aria-label="Consultation transcript">
          {turns.map((turn) => (
            <li key={turn.id} className={[styles.turn, styles[turn.role.toLowerCase()]].filter(Boolean).join(' ')}>
              <div className={styles.meta}>
                <span className={styles.speaker}>
                  {ROLE_LABELS[turn.role] ?? turn.role}
                </span>
                <time className={styles.timestamp} dateTime={turn.created_at}>
                  {formatTime(turn.created_at)}
                </time>
              </div>
              {/* lang="" left intentionally empty — non-Latin content will render 
                  via Noto Sans fallback automatically via font-family on body */}
              <p className={styles.text}>{turn.content}</p>
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}
