import type { ReactNode } from 'react';
import {
  CheckCircle,
  Warning,
  XCircle,
  Info,
  Clock,
  MicrophoneSlash,
} from '@phosphor-icons/react';
import styles from './Badge.module.css';

// ─── Generic Badge ───────────────────────────────────────────────────────────

export type BadgeVariant = 'default' | 'success' | 'warning' | 'critical' | 'info' | 'accent' | 'ai-draft';

export interface BadgeProps {
  variant?: BadgeVariant;
  children: ReactNode;
  className?: string;
}

/**
 * Badge — full radius chip for tags, status labels.
 * full-radius is only for chips/badges, NEVER for primary buttons.
 */
export function Badge({ variant = 'default', children, className }: BadgeProps) {
  return (
    <span
      className={[styles.badge, styles[variant], className ?? ''].filter(Boolean).join(' ')}
    >
      {children}
    </span>
  );
}

// ─── StatusBadge ─────────────────────────────────────────────────────────────

export type SeverityLevel = 'critical' | 'warning' | 'success' | 'info' | 'pending' | 'stockout';

const SEVERITY_CONFIG: Record<
  SeverityLevel,
  { icon: ReactNode; label: string; variant: BadgeVariant }
> = {
  critical:  { icon: <XCircle weight="fill" />,    label: 'Critical',  variant: 'critical' },
  warning:   { icon: <Warning weight="fill" />,    label: 'Warning',   variant: 'warning' },
  success:   { icon: <CheckCircle weight="fill" />, label: 'Confirmed', variant: 'success' },
  info:      { icon: <Info weight="fill" />,        label: 'Info',      variant: 'info' },
  pending:   { icon: <Clock weight="fill" />,       label: 'Pending',   variant: 'default' },
  stockout:  { icon: <MicrophoneSlash weight="fill" />, label: 'Stockout', variant: 'critical' },
};

export interface StatusBadgeProps {
  severity: SeverityLevel;
  /** Override the default label for this severity */
  label?: string;
  className?: string;
}

/**
 * StatusBadge — design.md § Components/Severity & triage badges
 * Always renders icon + text label + color. NEVER color alone.
 * This is a hard accessibility requirement, not a style preference.
 * critical color is reserved for genuine clinical urgency — never decorative.
 */
export function StatusBadge({ severity, label, className }: StatusBadgeProps) {
  const config = SEVERITY_CONFIG[severity];
  return (
    <Badge variant={config.variant} className={[styles.statusBadge, className ?? ''].filter(Boolean).join(' ')}>
      <span className={styles.statusIcon} aria-hidden="true">
        {config.icon}
      </span>
      <span>{label ?? config.label}</span>
    </Badge>
  );
}
