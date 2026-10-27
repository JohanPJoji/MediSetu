import type { InputHTMLAttributes, ReactNode } from 'react';
import styles from './Input.module.css';

export interface InputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'id'> {
  /** Required visible label — never use placeholder as the only label */
  label: string;
  id: string;
  error?: string;
  hint?: string;
  /** Optional icon rendered on the trailing edge */
  trailingIcon?: ReactNode;
}

/**
 * Input — design.md § Components/Inputs
 * Bottom-border-weighted (2px border-strong, thickens to accent on focus).
 * sm radius on top corners only. surface-muted fill.
 * EVERY input has a visible label — this is non-negotiable for accessibility
 * and for elderly/multilingual patient users.
 */
export function Input({
  label,
  id,
  error,
  hint,
  trailingIcon,
  className,
  ...props
}: InputProps) {
  return (
    <div className={[styles.wrapper, className ?? ''].filter(Boolean).join(' ')}>
      <label htmlFor={id} className={styles.label}>
        {label}
        {props.required && <span className={styles.required} aria-hidden="true"> *</span>}
      </label>
      <div className={styles.inputWrapper}>
        <input
          id={id}
          {...props}
          className={[styles.input, error ? styles.hasError : ''].filter(Boolean).join(' ')}
          aria-invalid={error ? 'true' : undefined}
          aria-describedby={
            [error ? `${id}-error` : '', hint ? `${id}-hint` : '']
              .filter(Boolean)
              .join(' ') || undefined
          }
        />
        {trailingIcon && (
          <span className={styles.trailingIcon} aria-hidden="true">
            {trailingIcon}
          </span>
        )}
      </div>
      {hint && !error && (
        <span id={`${id}-hint`} className={styles.hint}>
          {hint}
        </span>
      )}
      {error && (
        <span id={`${id}-error`} className={styles.error} role="alert">
          {error}
        </span>
      )}
    </div>
  );
}
