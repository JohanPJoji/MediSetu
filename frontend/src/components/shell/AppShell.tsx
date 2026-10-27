import { Outlet } from 'react-router-dom';
import type { AuthUser } from '../../lib/auth';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';
import styles from './AppShell.module.css';

interface AppShellProps {
  user: AuthUser;
  alertCount?: number;
}

/**
 * AppShell — design.md § Layout & Density by App
 *
 * Patient mode: calmer, roomier, mobile-first, single-column.
 * Clinical mode (DOCTOR/NURSE/PHARMACY/ADMIN): desktop-first, multi-pane,
 *   compact, sidebar always present.
 *
 * They share the sidebar and topbar — but the content area's max-width,
 * padding, and rhythm differ by data-density attribute.
 */
export function AppShell({ user, alertCount }: AppShellProps) {
  const isPatient = user.role === 'PATIENT';

  return (
    <div
      className={styles.shell}
      data-density={isPatient ? 'patient' : 'clinical'}
    >
      <Sidebar user={user} />

      <div className={styles.main}>
        <Topbar user={user} alertCount={alertCount} />

        <div className={styles.content}>
          <div
            className={[
              styles.contentInner,
              isPatient ? styles.patientContent : styles.clinicalContent,
            ].join(' ')}
          >
            <Outlet />
          </div>
        </div>
      </div>
    </div>
  );
}
