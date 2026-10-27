import { createBrowserRouter, Navigate } from 'react-router-dom';
import { RootLayout } from './RootLayout';
import { ProtectedRoute } from './ProtectedRoute';

// Auth
import { LoginPage } from '../features/auth/LoginPage';
import { RegisterPage } from '../features/auth/RegisterPage';

// Onboarding
import { PatientProfilePage } from '../features/onboarding/PatientProfilePage';

// Dashboard
import { DashboardPage } from '../features/dashboard/DashboardPage';

// Consultations
import { ConsultationListPage } from '../features/consultations/ConsultationListPage';
import { ConsultationDetailPage } from '../features/consultations/ConsultationDetailPage';

// Other features
import { LaboratoryPage } from '../features/laboratory/LaboratoryPage';
import { BillingPage } from '../features/billing/BillingPage';
import { InventoryPage } from '../features/inventory/InventoryPage';
import { PharmacyPage } from '../features/pharmacy/PharmacyPage';
import { ReferralsPage } from '../features/referrals/ReferralsPage';
import { AlertsPage } from '../features/alerts/AlertsPage';

export const router = createBrowserRouter([
  // ─── Public routes ────────────────────────────────────────────
  { path: '/login',    element: <LoginPage /> },
  { path: '/register', element: <RegisterPage /> },

  // ─── Authenticated routes ─────────────────────────────────────
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <RootLayout />,
        children: [
          // Default redirect
          { index: true, element: <Navigate to="/dashboard" replace /> },

          // Dashboard — all authenticated roles
          { path: '/dashboard', element: <DashboardPage /> },

          // Patient onboarding gate
          {
            path: '/onboarding',
            element: <ProtectedRoute roles={['PATIENT']} />,
            children: [{ index: true, element: <PatientProfilePage /> }],
          },

          // Consultations
          {
            path: '/consultations',
            element: <ProtectedRoute roles={['PATIENT', 'DOCTOR', 'NURSE', 'ADMIN']} />,
            children: [
              { index: true, element: <ConsultationListPage /> },
              { path: ':id', element: <ConsultationDetailPage /> },
            ],
          },

          // Laboratory
          {
            path: '/laboratory',
            element: <ProtectedRoute roles={['PATIENT', 'DOCTOR', 'NURSE', 'ADMIN']} />,
            children: [{ index: true, element: <LaboratoryPage /> }],
          },

          // Billing
          {
            path: '/billing',
            element: <ProtectedRoute roles={['PATIENT', 'ADMIN']} />,
            children: [{ index: true, element: <BillingPage /> }],
          },

          // Inventory
          {
            path: '/inventory',
            element: <ProtectedRoute roles={['PHARMACY', 'ADMIN']} />,
            children: [{ index: true, element: <InventoryPage /> }],
          },

          // Pharmacy
          {
            path: '/pharmacy',
            element: <ProtectedRoute roles={['DOCTOR', 'PHARMACY', 'ADMIN']} />,
            children: [{ index: true, element: <PharmacyPage /> }],
          },

          // Referrals
          {
            path: '/referrals',
            element: <ProtectedRoute roles={['PATIENT', 'DOCTOR', 'NURSE', 'ADMIN']} />,
            children: [{ index: true, element: <ReferralsPage /> }],
          },

          // Alerts
          {
            path: '/alerts',
            element: <ProtectedRoute roles={['ADMIN', 'PHARMACY']} />,
            children: [{ index: true, element: <AlertsPage /> }],
          },
        ],
      },
    ],
  },

  // ─── Fallback ─────────────────────────────────────────────────
  { path: '*', element: <Navigate to="/dashboard" replace /> },
]);
