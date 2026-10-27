import { Bell } from '@phosphor-icons/react';
import { Link } from 'react-router-dom';
import type { AuthUser } from '../../lib/auth';
import styles from './Topbar.module.css';

interface TopbarProps {
  user: AuthUser;
  alertCount?: number;
}

export function Topbar({ user, alertCount = 0 }: TopbarProps) {
  const showAlerts = user.role === 'ADMIN' || user.role === 'PHARMACY';

  return (
    <header className={styles.topbar} role="banner">
      <div className={styles.left}>
        {/* Page title injected via CSS — slot left empty for breadcrumb future use */}
      </div>
      <div className={styles.right}>
        {showAlerts && (
          <Link
            to="/alerts"
            className={styles.alertBtn}
            aria-label={`Alerts${alertCount > 0 ? `, ${alertCount} unread` : ''}`}
          >
            <Bell size={20} />
            {alertCount > 0 && (
              <span className={styles.alertBadge} aria-hidden="true">
                {alertCount > 99 ? '99+' : alertCount}
              </span>
            )}
          </Link>
        )}

        <div className={styles.userChip}>
          <span className={styles.avatar} aria-hidden="true">
            {user.full_name.charAt(0).toUpperCase()}
          </span>
          <span className={styles.userName}>{user.full_name}</span>
        </div>
      </div>
    </header>
  );
}
