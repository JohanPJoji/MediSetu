import { type ReactNode, useState } from 'react';
import { ArrowUp, ArrowDown } from '@phosphor-icons/react';
import styles from './Table.module.css';

export interface Column<T> {
  key: string;
  header: string;
  /** Set to true for ID/numeric columns — renders in Plex Mono */
  mono?: boolean;
  /** Allows sorting on this column */
  sortable?: boolean;
  /** Custom cell renderer */
  render?: (row: T) => ReactNode;
  /** Horizontal alignment */
  align?: 'left' | 'right' | 'center';
}

export interface TableProps<T extends Record<string, unknown>> {
  columns: Column<T>[];
  rows: T[];
  /** Key field for React reconciliation */
  rowKey: keyof T;
  /** Empty state message */
  emptyMessage?: string;
  /** Caption for accessibility */
  caption?: string;
  className?: string;
}

/**
 * Table — design.md § Components/Data tables (Doctor/Admin app)
 * Compact row height, border-strong hairline rules, sortable column headers
 * in label type, sticky header on scroll, monospace for numeric/ID columns.
 * No zebra-stripe by default — reserve for very long lists.
 */
export function Table<T extends Record<string, unknown>>({
  columns,
  rows,
  rowKey,
  emptyMessage = 'No data available.',
  caption,
  className,
}: TableProps<T>) {
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');

  const handleSort = (col: Column<T>) => {
    if (!col.sortable) return;
    if (sortKey === col.key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(col.key);
      setSortDir('asc');
    }
  };

  const sortedRows = sortKey
    ? [...rows].sort((a, b) => {
        const av = a[sortKey] as string;
        const bv = b[sortKey] as string;
        const cmp = String(av).localeCompare(String(bv), undefined, { numeric: true });
        return sortDir === 'asc' ? cmp : -cmp;
      })
    : rows;

  return (
    <div className={[styles.tableContainer, className ?? ''].filter(Boolean).join(' ')}>
      <table className={styles.table} role="table">
        {caption && <caption className={styles.caption}>{caption}</caption>}
        <thead className={styles.thead}>
          <tr>
            {columns.map((col) => (
              <th
                key={col.key}
                className={[
                  styles.th,
                  col.sortable ? styles.sortable : '',
                  col.mono ? styles.mono : '',
                  col.align === 'right' ? styles.alignRight : '',
                  col.align === 'center' ? styles.alignCenter : '',
                ]
                  .filter(Boolean)
                  .join(' ')}
                aria-sort={
                  sortKey === col.key
                    ? sortDir === 'asc'
                      ? 'ascending'
                      : 'descending'
                    : col.sortable
                    ? 'none'
                    : undefined
                }
                onClick={() => handleSort(col)}
                tabIndex={col.sortable ? 0 : undefined}
                onKeyDown={(e) => {
                  if (col.sortable && (e.key === 'Enter' || e.key === ' ')) {
                    e.preventDefault();
                    handleSort(col);
                  }
                }}
              >
                <span className={styles.thContent}>
                  {col.header}
                  {col.sortable && (
                    <span className={styles.sortIcon} aria-hidden="true">
                      {sortKey === col.key ? (
                        sortDir === 'asc' ? <ArrowUp size={12} /> : <ArrowDown size={12} />
                      ) : (
                        <ArrowUp size={12} style={{ opacity: 0.3 }} />
                      )}
                    </span>
                  )}
                </span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sortedRows.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className={styles.empty}>
                {emptyMessage}
              </td>
            </tr>
          ) : (
            sortedRows.map((row) => (
              <tr key={String(row[rowKey])} className={styles.tr}>
                {columns.map((col) => (
                  <td
                    key={col.key}
                    className={[
                      styles.td,
                      col.mono ? styles.mono : '',
                      col.align === 'right' ? styles.alignRight : '',
                      col.align === 'center' ? styles.alignCenter : '',
                    ]
                      .filter(Boolean)
                      .join(' ')}
                  >
                    {col.render ? col.render(row) : String(row[col.key] ?? '')}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
