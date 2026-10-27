import { useEffect, useState } from 'react';
import { Package, WarningCircle } from '@phosphor-icons/react';
import { api } from '../../lib/api';
import { StatusBadge } from '../../components/primitives/Badge';
import { EmptyState } from '../../components/primitives/EmptyState';
import { useToast } from '../../components/primitives/Toast';
import { Table } from '../../components/primitives/Table';
import styles from './InventoryPage.module.css';

interface InventoryItem {
  id: string;
  medicine_name: string;
  stock_quantity: number;
  batch_number: string;
  expiry_date: string;
}

function formatDate(iso: string) {
  try { return new Date(iso).toLocaleDateString([], { dateStyle: 'medium' }); }
  catch { return iso; }
}

export function InventoryPage() {
  const { toast } = useToast();
  const [items, setItems]       = useState<InventoryItem[]>([]);
  const [loading, setLoading]   = useState(true);

  useEffect(() => {
    api.inventory()
      .then((r) => setItems(r.data as InventoryItem[]))
      .catch((err) => toast({ severity: 'warning', title: 'Could not load inventory', message: err instanceof Error ? err.message : undefined }))
      .finally(() => setLoading(false));
  }, []);

  const getStockSeverity = (qty: number) => {
    if (qty <= 0) return 'critical';
    if (qty < 20) return 'warning';
    return 'success';
  };

  const getExpirySeverity = (date: string) => {
    const msToExpiry = new Date(date).getTime() - Date.now();
    const daysToExpiry = msToExpiry / (1000 * 60 * 60 * 24);
    if (daysToExpiry <= 0) return 'critical';
    if (daysToExpiry <= 30) return 'warning';
    return 'success';
  };

  const columns = [
    {
      key: 'medicine_name',
      header: 'Medicine',
      sortable: true,
      render: (row: InventoryItem) => <span className={styles.nameCell}>{row.medicine_name}</span>,
    },
    {
      key: 'stock_quantity',
      header: 'Stock',
      sortable: true,
      render: (row: InventoryItem) => (
        <StatusBadge
          severity={getStockSeverity(row.stock_quantity)}
          label={row.stock_quantity.toString()}
        />
      ),
    },
    {
      key: 'batch_number',
      header: 'Batch',
      mono: true,
    },
    {
      key: 'expiry_date',
      header: 'Expiry',
      sortable: true,
      render: (row: InventoryItem) => (
        <span className={getExpirySeverity(row.expiry_date) === 'critical' ? styles.expired : ''}>
          {formatDate(row.expiry_date)}
          {getExpirySeverity(row.expiry_date) === 'critical' && <WarningCircle className={styles.warnIcon} size={14} />}
        </span>
      ),
    },
  ];

  return (
    <div className={styles.page}>
      <div className={styles.pageHeader}>
        <h1 className={styles.title}>Inventory</h1>
      </div>

      {loading ? (
        <p className={styles.loadingText}>Loading inventory…</p>
      ) : items.length === 0 ? (
        <EmptyState
          icon={<Package size={40} />}
          title="No inventory records"
          description="Medicine stock will appear here."
        />
      ) : (
        <div className={styles.tableWrapper}>
          <Table
            columns={columns as any}
            rows={items as any}
            rowKey="id"
            caption="Current medicine stock levels"
          />
        </div>
      )}
    </div>
  );
}
