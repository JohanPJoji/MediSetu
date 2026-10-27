import type { ReactNode } from 'react';
import styles from './EmptyState.module.css';

export interface EmptyStateProps {
  title: string;
  description?: string;
  action?: ReactNode;
  /** Optional Phosphor icon */
  icon?: ReactNode;
}

/**
 * EmptyState — design.md § Empty & error states
 * Plain language, tells the user what happened and what to do next.
 * No emoji, no apology, no "Looks like it's quiet here! 🎉"
 */
export function EmptyState({ title, description, action, icon }: EmptyStateProps) {
  return (
    <div className={styles.wrapper}>
      {icon && (
        <span className={styles.icon} aria-hidden="true">
          {icon}
        </span>
      )}
      <h3 className={styles.title}>{title}</h3>
      {description && <p className={styles.description}>{description}</p>}
      {action && <div className={styles.action}>{action}</div>}
    </div>
  );
}
