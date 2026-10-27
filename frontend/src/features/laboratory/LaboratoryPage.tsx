import { useEffect, useState } from 'react';
import { Flask, Plus } from '@phosphor-icons/react';
import { api } from '../../lib/api';
import { useAuth } from '../../app/AuthContext';
import { Button } from '../../components/primitives/Button';
import { StatusBadge } from '../../components/primitives/Badge';
import { EmptyState } from '../../components/primitives/EmptyState';
import { Modal } from '../../components/primitives/Modal';
import { Input } from '../../components/primitives/Input';
import { Select } from '../../components/primitives/Select';
import { useToast } from '../../components/primitives/Toast';
import styles from './LaboratoryPage.module.css';

interface LabTest { id: string; test_name: string; status: string; result?: string; created_at?: string; }

function statusSev(s: string) {
  switch (s?.toUpperCase()) {
    case 'COMPLETED': return 'success' as const;
    case 'PENDING':   return 'pending' as const;
    case 'CANCELLED': return 'info'    as const;
    default:          return 'pending' as const;
  }
}

const TEST_OPTIONS = [
  { value: 'CBC',         label: 'Complete Blood Count (CBC)' },
  { value: 'BMP',         label: 'Basic Metabolic Panel (BMP)' },
  { value: 'LFT',         label: 'Liver Function Test (LFT)' },
  { value: 'LIPID',       label: 'Lipid Profile' },
  { value: 'HBA1C',       label: 'HbA1c (Diabetes monitoring)' },
  { value: 'URINE_CULTURE', label: 'Urine Culture' },
  { value: 'XRAY_CHEST',  label: 'Chest X-Ray' },
  { value: 'ECG',         label: 'Electrocardiogram (ECG)' },
  { value: 'OTHER',       label: 'Other (specify in notes)' },
];

function formatDate(iso?: string) {
  if (!iso) return '—';
  try { return new Date(iso).toLocaleDateString([], { dateStyle: 'medium' }); }
  catch { return iso; }
}

export function LaboratoryPage() {
  const { user } = useAuth();
  const { toast } = useToast();
  const [tests, setTests]       = useState<LabTest[]>([]);
  const [loading, setLoading]   = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [creating, setCreating] = useState(false);
  const [consultId, setConsultId] = useState('');
  const [testName, setTestName]   = useState('CBC');
  const [customName, setCustomName] = useState('');

  const isPatient  = user?.role === 'PATIENT';
  const canOrder   = ['DOCTOR', 'NURSE', 'ADMIN'].includes(user?.role ?? '');

  const load = async () => {
    setLoading(true);
    try {
      const r = await api.labTests();
      setTests(r.data as LabTest[]);
    } catch (err) {
      toast({ severity: 'warning', title: 'Could not load lab tests', message: err instanceof Error ? err.message : undefined });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleOrder = async () => {
    setCreating(true);
    try {
      const name = testName === 'OTHER' ? customName.trim() : testName;
      await api.orderLabTest(consultId.trim(), name);
      toast({ severity: 'success', title: 'Lab test ordered' });
      setShowModal(false);
      setConsultId('');
      setTestName('CBC');
      setCustomName('');
      await load();
    } catch (err) {
      toast({ severity: 'critical', title: 'Failed to order lab test', message: err instanceof Error ? err.message : undefined, persistent: true });
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className={styles.page}>
      <div className={styles.pageHeader}>
        <h1 className={styles.title}>Laboratory</h1>
        {canOrder && (
          <Button variant="primary" icon={<Plus size={16} />} onClick={() => setShowModal(true)}>
            Order test
          </Button>
        )}
      </div>

      {loading ? (
        <p className={styles.loadingText}>Loading lab tests…</p>
      ) : tests.length === 0 ? (
        <EmptyState
          icon={<Flask size={40} />}
          title="No lab tests"
          description={isPatient ? 'Your doctor will order lab tests when needed. Results appear here.' : 'No lab tests have been ordered yet.'}
        />
      ) : (
        <div className={styles.testList}>
          {tests.map((t) => (
            <div key={t.id} className={styles.testCard}>
              <div className={styles.testHeader}>
                <span className={styles.testName}>{t.test_name}</span>
                <StatusBadge severity={statusSev(t.status)} label={t.status ?? 'PENDING'} />
              </div>
              <div className={styles.testMeta}>
                <span className={styles.testId}>{t.id.slice(0, 8)}…</span>
                <span className={styles.testDate}>{formatDate(t.created_at)}</span>
              </div>
              {t.result && (
                <div className={styles.testResult}>
                  <span className={styles.resultLabel}>Result</span>
                  <p className={styles.resultText}>{t.result}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      <Modal
        open={showModal}
        onClose={() => setShowModal(false)}
        title="Order lab test"
        footer={
          <>
            <Button variant="ghost" onClick={() => setShowModal(false)}>Cancel</Button>
            <Button
              variant="primary"
              loading={creating}
              onClick={handleOrder}
              disabled={!consultId.trim() || (testName === 'OTHER' && !customName.trim())}
            >
              Order
            </Button>
          </>
        }
      >
        <div className={styles.modalBody}>
          <Input
            id="lab-consult-id"
            label="Consultation ID (UUID)"
            value={consultId}
            onChange={(e) => setConsultId(e.target.value)}
            placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
            required
          />
          <Select
            id="lab-test-name"
            label="Test"
            options={TEST_OPTIONS}
            value={testName}
            onChange={(e) => setTestName(e.target.value)}
            required
          />
          {testName === 'OTHER' && (
            <Input
              id="lab-custom-name"
              label="Test name"
              value={customName}
              onChange={(e) => setCustomName(e.target.value)}
              placeholder="Specify test name"
              required
            />
          )}
        </div>
      </Modal>
    </div>
  );
}
