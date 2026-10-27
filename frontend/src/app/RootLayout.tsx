import { useState, useEffect } from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from './AuthContext';
import { AppShell } from '../components/shell/AppShell';
import { api } from '../lib/api';

/**
 * RootLayout — the authenticated layout wrapper.
 * Fetches the alert count for the topbar bell and renders AppShell
 * which switches between patient and clinical density modes.
 */
export function RootLayout() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [alertCount, setAlertCount] = useState(0);

  useEffect(() => {
    if (!user) return;
    if (user.role === 'ADMIN' || user.role === 'PHARMACY') {
      api.alerts()
        .then((r) => setAlertCount(Array.isArray(r.data) ? r.data.length : 0))
        .catch(() => {});
    }
  }, [user]);

  if (!user) {
    navigate('/login', { replace: true });
    return null;
  }

  return <AppShell user={user} alertCount={alertCount} />;
}
