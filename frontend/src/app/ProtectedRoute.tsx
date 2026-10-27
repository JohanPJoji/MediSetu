import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from './AuthContext';
import type { Role } from '../lib/api';

interface ProtectedRouteProps {
  /** If provided, user must have one of these roles to access this route */
  roles?: Role[];
}

/**
 * ProtectedRoute — gate based on:
 * 1. Authentication: if no token or user load failed → /login
 * 2. Role: if user's role is not in allowedRoles → /dashboard (soft redirect)
 */
export function ProtectedRoute({ roles }: ProtectedRouteProps) {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          background: 'var(--color-background)',
          fontFamily: 'var(--font-sans)',
          color: 'var(--color-foreground-muted)',
          fontSize: 'var(--text-body)',
        }}
      >
        Loading…
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (roles && !roles.includes(user.role)) {
    return <Navigate to="/dashboard" replace />;
  }

  return <Outlet />;
}
