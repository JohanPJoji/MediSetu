import {
  createContext,
  useCallback,
  useContext,
  useRef,
  useState,
  type ReactNode,
} from 'react';
import { createPortal } from 'react-dom';
import { CheckCircle, Warning, XCircle, Info, X } from '@phosphor-icons/react';
import styles from './Toast.module.css';

// ─── Types ────────────────────────────────────────────────────────────────────

export type ToastSeverity = 'success' | 'warning' | 'critical' | 'info';

export interface ToastItem {
  id: string;
  severity: ToastSeverity;
  title: string;
  message?: string;
  /** If true, stays until explicitly dismissed — required for critical alerts */
  persistent?: boolean;
  /** Auto-dismiss after ms (default: 5000 for non-critical) */
  duration?: number;
}

// ─── Context ──────────────────────────────────────────────────────────────────

interface ToastContextValue {
  toast: (item: Omit<ToastItem, 'id'>) => void;
  dismiss: (id: string) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used inside <ToastProvider>');
  return ctx;
}

// ─── Provider ─────────────────────────────────────────────────────────────────

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const timers = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());

  const dismiss = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
    const timer = timers.current.get(id);
    if (timer) {
      clearTimeout(timer);
      timers.current.delete(id);
    }
  }, []);

  const toast = useCallback(
    (item: Omit<ToastItem, 'id'>) => {
      const id = crypto.randomUUID();
      const newToast: ToastItem = { id, ...item };
      setToasts((prev) => [newToast, ...prev].slice(0, 5)); // max 5 toasts

      // Critical and persistent toasts do NOT auto-dismiss — design.md § Notifications
      if (!newToast.persistent && newToast.severity !== 'critical') {
        const duration = newToast.duration ?? 5000;
        const timer = setTimeout(() => dismiss(id), duration);
        timers.current.set(id, timer);
      }
    },
    [dismiss]
  );

  return (
    <ToastContext.Provider value={{ toast, dismiss }}>
      {children}
      {createPortal(<ToastRegion toasts={toasts} onDismiss={dismiss} />, document.body)}
    </ToastContext.Provider>
  );
}

// ─── Toast Region (rendered via portal) ──────────────────────────────────────

const ICONS: Record<ToastSeverity, ReactNode> = {
  success:  <CheckCircle weight="fill" size={20} />,
  warning:  <Warning weight="fill" size={20} />,
  critical: <XCircle weight="fill" size={20} />,
  info:     <Info weight="fill" size={20} />,
};

function ToastRegion({
  toasts,
  onDismiss,
}: {
  toasts: ToastItem[];
  onDismiss: (id: string) => void;
}) {
  if (toasts.length === 0) return null;

  return (
    <div className={styles.region} aria-live="polite" aria-atomic="false">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={[styles.toast, styles[t.severity]].join(' ')}
          role={t.severity === 'critical' ? 'alert' : 'status'}
        >
          <span className={styles.icon} aria-hidden="true">
            {ICONS[t.severity]}
          </span>
          <div className={styles.content}>
            <p className={styles.title}>{t.title}</p>
            {t.message && <p className={styles.message}>{t.message}</p>}
          </div>
          <button
            type="button"
            className={styles.dismissBtn}
            onClick={() => onDismiss(t.id)}
            aria-label={`Dismiss: ${t.title}`}
          >
            <X size={16} />
          </button>
        </div>
      ))}
    </div>
  );
}
