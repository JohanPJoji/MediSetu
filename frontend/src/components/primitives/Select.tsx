import type { SelectHTMLAttributes } from 'react';
import styles from './Select.module.css';

export interface SelectOption {
  value: string;
  label: string;
}

export interface SelectProps extends Omit<SelectHTMLAttributes<HTMLSelectElement>, 'id'> {
  label: string;
  id: string;
  options: SelectOption[];
  error?: string;
  hint?: string;
  placeholder?: string;
}

/**
 * Select — same bottom-border-weighted treatment as Input.
 * Every select has a visible label — same accessibility requirement.
 */
export function Select({
  label,
  id,
  options,
  error,
  hint,
  placeholder,
  className,
  ...props
}: SelectProps) {
  return (
    <div className={[styles.wrapper, className ?? ''].filter(Boolean).join(' ')}>
      <label htmlFor={id} className={styles.label}>
        {label}
        {props.required && <span className={styles.required} aria-hidden="true"> *</span>}
      </label>
      <div className={styles.selectWrapper}>
        <select
          id={id}
          {...props}
          className={[styles.select, error ? styles.hasError : ''].filter(Boolean).join(' ')}
          aria-invalid={error ? 'true' : undefined}
          aria-describedby={
            [error ? `${id}-error` : '', hint ? `${id}-hint` : '']
              .filter(Boolean)
              .join(' ') || undefined
          }
        >
          {placeholder && (
            <option value="" disabled>
              {placeholder}
            </option>
          )}
          {options.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        <span className={styles.chevron} aria-hidden="true">
          ▾
        </span>
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
