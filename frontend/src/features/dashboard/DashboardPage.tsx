import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../app/AuthContext';
import { Button } from '../../components/primitives/Button';
import { Stethoscope, Flask, Receipt, Package, Pill, ArrowsClockwise, Bell } from '@phosphor-icons/react';
import type { Role } from '../../lib/api';
import styles from './DashboardPage.module.css';

interface QuickLink {
  to: string;
  label: string;
  description: string;
  icon: React.ReactNode;
  roles: Role[];
}

const QUICK_LINKS: QuickLink[] = [
  {
    to: '/consultations',
    label: 'Consultations',
    description: 'Start a consultation or view your consultation history.',
    icon: <Stethoscope size={24} />,
    roles: ['PATIENT', 'DOCTOR', 'NURSE', 'ADMIN'],
  },
  {
    to: '/laboratory',
    label: 'Laboratory',
    description: 'View lab tests and your test orders.',
    icon: <Flask size={24} />,
    roles: ['PATIENT', 'DOCTOR', 'NURSE', 'ADMIN'],
  },
  {
    to: '/billing',
    label: 'Billing',
    description: 'View your bills and payment history.',
    icon: <Receipt size={24} />,
    roles: ['PATIENT', 'ADMIN'],
  },
  {
    to: '/pharmacy',
    label: 'Pharmacy',
    description: 'Manage medicines, prescriptions, and orders.',
    icon: <Pill size={24} />,
    roles: ['DOCTOR', 'PHARMACY', 'ADMIN'],
  },
  {
    to: '/inventory',
    label: 'Inventory',
    description: 'Track medicine stock levels and batch expiry.',
    icon: <Package size={24} />,
    roles: ['PHARMACY', 'ADMIN'],
  },
  {
    to: '/referrals',
    label: 'Referrals',
    description: 'View patient referrals and their status.',
    icon: <ArrowsClockwise size={24} />,
    roles: ['PATIENT', 'DOCTOR', 'NURSE', 'ADMIN'],
  },
  {
    to: '/alerts',
    label: 'Alerts',
    description: 'Medicine stock alerts that require your attention.',
    icon: <Bell size={24} />,
    roles: ['ADMIN', 'PHARMACY'],
  },
];

export function DashboardPage() {
  const { user } = useAuth();
  const navigate = useNavigate();

  if (!user) return null;

  const isPatient = user.role === 'PATIENT';
  const links = QUICK_LINKS.filter((l) => l.roles.includes(user.role));

  return (
    <div className={[styles.page, isPatient ? styles.patient : styles.clinical].join(' ')}>
      <div className={styles.welcome}>
        <h1 className={styles.greeting}>
          {isPatient ? 'Welcome back' : 'Dashboard'}
        </h1>
        {isPatient && (
          <p className={styles.welcomeText}>
            {user.full_name}, your health information is here when you need it.
          </p>
        )}
        {!isPatient && (
          <p className={styles.welcomeText}>
            {user.full_name} — {user.role.charAt(0) + user.role.slice(1).toLowerCase()} view
          </p>
        )}
      </div>

      {isPatient && (
        <div className={styles.primaryAction}>
          <Button
            variant="primary"
            size="lg"
            onClick={() => navigate('/consultations')}
          >
            Start a consultation
          </Button>
          <p className={styles.primaryActionHint}>
            Speak with an AI assistant first — a doctor will review everything.
          </p>
        </div>
      )}

      <div className={[styles.grid, isPatient ? styles.patientGrid : styles.clinicalGrid].join(' ')}>
        {links.map((link) => (
          <button
            key={link.to}
            type="button"
            className={styles.quickCard}
            onClick={() => navigate(link.to)}
          >
            <span className={styles.quickIcon} aria-hidden="true">
              {link.icon}
            </span>
            <span className={styles.quickLabel}>{link.label}</span>
            <span className={styles.quickDesc}>{link.description}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
