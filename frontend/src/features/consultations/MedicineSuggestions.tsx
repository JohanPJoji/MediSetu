import { useState } from 'react';
import { Robot, CheckCircle, ArrowsClockwise } from '@phosphor-icons/react';
import { Button } from '../../components/primitives/Button';
import { EmptyState } from '../../components/primitives/EmptyState';
import styles from './MedicineSuggestions.module.css';

interface Suggestion {
  name: string;
  dosage?: string;
  frequency?: string;
  duration?: string;
  notes?: string;
}

type ItemState = 'ai-suggested' | 'alternative' | 'confirmed';

interface SuggestionItem extends Suggestion {
  state: ItemState;
}

interface MedicineSuggestionsProps {
  consultationId: string;
  onFetch: () => Promise<Suggestion[]>;
  /** Only doctors can see and confirm suggestions */
  canFetch: boolean;
}

/**
 * MedicineSuggestions — design.md § The AI-Draft vs. Confirmed System
 *
 * Three states per suggestion (non-negotiable — patient safety):
 *
 * AI-SUGGESTED: amber draft treatment — icon + "AI-suggested" label + amber bg.
 * ALTERNATIVE:  doctor has chosen a different option — intermediate state.
 * CONFIRMED:    teal confirmed treatment — icon + "Confirmed" label + teal border.
 *
 * State is local-only (no backend persist endpoint) — see gaps list.
 */
export function MedicineSuggestions({ onFetch, canFetch }: MedicineSuggestionsProps) {
  const [items, setItems]     = useState<SuggestionItem[]>([]);
  const [fetching, setFetching] = useState(false);
  const [fetched, setFetched]  = useState(false);
  const [error, setError]      = useState('');

  const handleFetch = async () => {
    setError('');
    setFetching(true);
    try {
      const suggestions = await onFetch();
      setItems(suggestions.map((s) => ({ ...s, state: 'ai-suggested' as ItemState })));
      setFetched(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not load AI suggestions.');
    } finally {
      setFetching(false);
    }
  };

  const updateState = (idx: number, newState: ItemState) => {
    setItems((prev) => prev.map((item, i) => i === idx ? { ...item, state: newState } : item));
  };

  if (!canFetch) return null;

  return (
    <div className={styles.panel}>
      <div className={styles.panelHeader}>
        <span>Medicine Suggestions</span>
        <span className={styles.doctorOnly}>Doctor only</span>
      </div>

      <div className={styles.panelBody}>
        {error && <div className={styles.errorBox} role="alert">{error}</div>}

        {!fetched ? (
          <EmptyState
            title="No suggestions loaded"
            description="Fetch AI-suggested medicines based on this consultation's clinical history."
            action={
              <Button variant="secondary" loading={fetching} onClick={handleFetch}>
                Load AI suggestions
              </Button>
            }
          />
        ) : items.length === 0 ? (
          <EmptyState
            title="No suggestions available"
            description="AI suggestions require an external LLM provider configured in the backend."
          />
        ) : (
          <ul className={styles.list} aria-label="Medicine suggestions">
            {items.map((item, idx) => (
              <li
                key={idx}
                className={[
                  styles.item,
                  item.state === 'ai-suggested' ? styles.aiItem :
                  item.state === 'alternative'  ? styles.altItem :
                                                  styles.confirmedItem,
                ].join(' ')}
              >
                {/* State badge — icon + label + color, NEVER color alone */}
                <div className={styles.itemHeader}>
                  <div className={styles.itemName}>{item.name}</div>
                  {item.state === 'ai-suggested' && (
                    <span className={styles.aiBadge}>
                      <Robot size={12} aria-hidden="true" /> AI-suggested
                    </span>
                  )}
                  {item.state === 'alternative' && (
                    <span className={styles.altBadge}>
                      <ArrowsClockwise size={12} aria-hidden="true" /> Alternative selected
                    </span>
                  )}
                  {item.state === 'confirmed' && (
                    <span className={styles.confirmedBadge}>
                      <CheckCircle size={12} weight="fill" aria-hidden="true" /> Confirmed
                    </span>
                  )}
                </div>

                <div className={styles.itemMeta}>
                  {item.dosage    && <span><strong>Dosage:</strong> {item.dosage}</span>}
                  {item.frequency && <span><strong>Frequency:</strong> {item.frequency}</span>}
                  {item.duration  && <span><strong>Duration:</strong> {item.duration}</span>}
                  {item.notes     && <span className={styles.notes}>{item.notes}</span>}
                </div>

                <div className={styles.itemActions}>
                  {item.state !== 'confirmed' && (
                    <Button
                      variant="primary"
                      size="sm"
                      icon={<CheckCircle size={14} />}
                      onClick={() => updateState(idx, 'confirmed')}
                    >
                      Confirm
                    </Button>
                  )}
                  {item.state === 'ai-suggested' && (
                    <Button
                      variant="ghost"
                      size="sm"
                      icon={<ArrowsClockwise size={14} />}
                      onClick={() => updateState(idx, 'alternative')}
                    >
                      Mark as alternative
                    </Button>
                  )}
                  {item.state === 'confirmed' && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => updateState(idx, 'ai-suggested')}
                    >
                      Undo
                    </Button>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}

        {fetched && items.length > 0 && (
          <Button variant="ghost" size="sm" loading={fetching} onClick={handleFetch}>
            Reload suggestions
          </Button>
        )}
      </div>
    </div>
  );
}
