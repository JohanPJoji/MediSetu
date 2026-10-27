import { useState } from 'react';
import { CheckCircle, Robot, PencilSimple } from '@phosphor-icons/react';
import { Button } from '../../components/primitives/Button';
import { EmptyState } from '../../components/primitives/EmptyState';
import styles from './SummaryPanel.module.css';

interface SummaryData {
  summary?: string;
  key_points?: string[];
}

type SummaryState = 'empty' | 'draft' | 'confirmed';

interface SummaryPanelProps {
  consultationId: string;
  onGenerate: () => Promise<SummaryData | null>;
  canGenerate: boolean;
}

/**
 * SummaryPanel — design.md § The AI-Draft vs. Confirmed System
 *
 * Three states (non-negotiable — patient safety requirement):
 *
 * EMPTY: no summary yet — show "Generate AI summary" action.
 *
 * AI-DRAFT: ai-draft-bg wash, 3px left border in ai-draft amber,
 *   "AI-suggested" label + Robot icon, editable text with dashed underline.
 *   This is visually DISTINCT from confirmed — by label, icon, AND color.
 *
 * CONFIRMED: plain surface, 3px left border in confirmed teal,
 *   "Confirmed" label + CheckCircle icon, dashed underline removed.
 *   Also distinct by label, icon, AND color.
 *
 * Color is NOT the only distinguishing factor (grayscale / colorblind safety).
 *
 * NOTE: Confirmation is client-side only — no backend persist endpoint exists yet.
 * See gaps list in implementation_plan.md.
 */
export function SummaryPanel({ onGenerate, canGenerate }: SummaryPanelProps) {
  const [state, setState]     = useState<SummaryState>('empty');
  const [data, setData]       = useState<SummaryData | null>(null);
  const [editedSummary, setEditedSummary] = useState('');
  const [generating, setGenerating] = useState(false);
  const [error, setError]     = useState('');

  const handleGenerate = async () => {
    setError('');
    setGenerating(true);
    try {
      const result = await onGenerate();
      if (result) {
        setData(result);
        setEditedSummary(result.summary ?? '');
        setState('draft');
      } else {
        setError('No summary available. Ensure the consultation has a transcript first.');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not generate summary.');
    } finally {
      setGenerating(false);
    }
  };

  const handleConfirm = () => {
    setData((prev) => prev ? { ...prev, summary: editedSummary } : prev);
    setState('confirmed');
  };

  const handleReopen = () => {
    setState('draft');
  };

  if (state === 'empty') {
    return (
      <div className={styles.panel}>
        <div className={styles.panelHeader}>Clinical Summary</div>
        <div className={styles.panelBody}>
          {error && <div className={styles.errorBox} role="alert">{error}</div>}
          <EmptyState
            title="No summary yet"
            description="Generate an AI-assisted summary of this consultation for clinical review."
            action={
              canGenerate ? (
                <Button
                  variant="primary"
                  onClick={handleGenerate}
                  loading={generating}
                >
                  Generate AI summary
                </Button>
              ) : undefined
            }
          />
        </div>
      </div>
    );
  }

  return (
    <div className={[styles.panel, state === 'draft' ? styles.draftPanel : styles.confirmedPanel].join(' ')}>
      <div className={styles.panelHeader}>
        <span>Clinical Summary</span>
        {/* State indicator: icon + label — never color alone */}
        {state === 'draft' ? (
          <span className={styles.draftBadge}>
            <Robot size={14} aria-hidden="true" />
            AI-suggested
          </span>
        ) : (
          <span className={styles.confirmedBadge}>
            <CheckCircle size={14} weight="fill" aria-hidden="true" />
            Confirmed
          </span>
        )}
      </div>

      <div className={styles.panelBody}>
        {error && <div className={styles.errorBox} role="alert">{error}</div>}

        {/* Summary text — editable in draft mode (dashed underline cue) */}
        <div className={styles.summarySection}>
          <label htmlFor="summary-text" className={styles.fieldLabel}>Summary</label>
          {state === 'draft' ? (
            <textarea
              id="summary-text"
              className={styles.summaryTextarea}
              value={editedSummary}
              onChange={(e) => setEditedSummary(e.target.value)}
              rows={5}
              aria-label="AI-suggested summary — editable before confirming"
            />
          ) : (
            <p className={styles.summaryText} aria-label="Confirmed summary">
              {editedSummary}
            </p>
          )}
        </div>

        {/* Key points */}
        {data?.key_points && data.key_points.length > 0 && (
          <div className={styles.keyPoints}>
            <p className={styles.fieldLabel}>Key points</p>
            <ul className={styles.keyList} aria-label="Key points from summary">
              {data.key_points.map((point, i) => (
                <li key={i} className={styles.keyPoint}>
                  <span className={styles.bullet} aria-hidden="true">—</span>
                  {point}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Actions */}
        <div className={styles.actions}>
          {state === 'draft' && (
            <Button variant="primary" icon={<CheckCircle size={16} />} onClick={handleConfirm}>
              Confirm summary
            </Button>
          )}
          {state === 'confirmed' && (
            <Button variant="ghost" icon={<PencilSimple size={16} />} onClick={handleReopen}>
              Re-open for editing
            </Button>
          )}
          <Button
            variant="ghost"
            loading={generating}
            onClick={handleGenerate}
          >
            Regenerate
          </Button>
        </div>
      </div>
    </div>
  );
}
