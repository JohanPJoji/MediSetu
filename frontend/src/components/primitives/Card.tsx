import type { HTMLAttributes, ReactNode } from 'react';
import styles from './Card.module.css';

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  /** Adds bottom padding and a bottom divider to the header slot */
  header?: ReactNode;
  /** Optional footer slot */
  footer?: ReactNode;
  /** Remove padding for tables or custom content that bleeds to edge */
  noPadding?: boolean;
}

/**
 * Card — design.md § Components/Cards
 * Surface background, 1px border, md radius (8px), no shadow at rest.
 * Used to group related information, not as decoration around every element.
 */
export function Card({ header, footer, noPadding, children, className, ...props }: CardProps) {
  return (
    <div
      {...props}
      className={[styles.card, noPadding ? styles.noPadding : '', className ?? ''].filter(Boolean).join(' ')}
    >
      {header && <div className={styles.header}>{header}</div>}
      <div className={styles.body}>{children}</div>
      {footer && <div className={styles.footer}>{footer}</div>}
    </div>
  );
}
