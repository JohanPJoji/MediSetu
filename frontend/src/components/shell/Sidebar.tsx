import { NavLink, useNavigate } from 'react-router-dom';
import {
  House,
  Stethoscope,
  Flask,
  Receipt,
  Package,
  Pill,
  ArrowsClockwise,
  Bell,
  SignOut,
} from '@phosphor-icons/react';
import type { AuthUser } from '../../lib/auth';
import { auth } from '../../lib/auth';
import type { Role } from '../../lib/api';
import styles from './Sidebar.module.css';

interface NavItem {
  to: string;
  label: string;
  icon: React.ReactNode;
}

const ALL_NAV: NavItem[] = [
  { to: '/dashboard',    label: 'Dashboard',    icon: <House size={18} /> },
  { to: '/consultations',label: 'Consultations',icon: <Stethoscope size={18} /> },
  { to: '/laboratory',   label: 'Laboratory',   icon: <Flask size={18} /> },
  { to: '/billing',      label: 'Billing',      icon: <Receipt size={18} /> },
  { to: '/inventory',    label: 'Inventory',    icon: <Package size={18} /> },
  { to: '/pharmacy',     label: 'Pharmacy',     icon: <Pill size={18} /> },
  { to: '/referrals',    label: 'Referrals',    icon: <ArrowsClockwise size={18} /> },
  { to: '/alerts',       label: 'Alerts',       icon: <Bell size={18} /> },
];

const ROLE_ROUTES: Record<Role, string[]> = {
  PATIENT:  ['/dashboard', '/consultations', '/laboratory', '/billing', '/referrals'],
  DOCTOR:   ['/dashboard', '/consultations', '/laboratory', '/pharmacy', '/referrals'],
  NURSE:    ['/dashboard', '/consultations', '/laboratory', '/referrals'],
  PHARMACY: ['/dashboard', '/pharmacy', '/inventory'],
  ADMIN:    ['/dashboard', '/consultations', '/laboratory', '/billing', '/inventory', '/pharmacy', '/referrals', '/alerts'],
};

interface SidebarProps {
  user: AuthUser;
}

export function Sidebar({ user }: SidebarProps) {
  const navigate = useNavigate();
  const allowed = ROLE_ROUTES[user.role];
  const navItems = ALL_NAV.filter((n) => allowed.includes(n.to));

  const handleSignOut = () => {
    auth.clear();
    navigate('/login', { replace: true });
  };

  return (
    <nav className={styles.sidebar} aria-label="Main navigation">
      <div className={styles.brand}>
        <span className={styles.brandMark}>M</span>
        <span className={styles.brandName}>MediSetu</span>
      </div>

      <div className={styles.userInfo}>
        <p className={styles.userName}>{user.full_name}</p>
        <span className={styles.roleChip}>{user.role}</span>
      </div>

      <ul className={styles.navList} role="list">
        {navItems.map((item) => (
          <li key={item.to}>
            <NavLink
              to={item.to}
              className={({ isActive }) =>
                [styles.navLink, isActive ? styles.active : ''].filter(Boolean).join(' ')
              }
            >
              <span className={styles.navIcon} aria-hidden="true">
                {item.icon}
              </span>
              <span>{item.label}</span>
            </NavLink>
          </li>
        ))}
      </ul>

      <button
        type="button"
        className={styles.signOut}
        onClick={handleSignOut}
      >
        <span aria-hidden="true"><SignOut size={18} /></span>
        <span>Sign out</span>
      </button>
    </nav>
  );
}
