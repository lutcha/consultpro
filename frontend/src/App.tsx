// ============================================
// APP - Main Application Component
// ============================================

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { useUserStore } from '@/stores';
import {
  LandingPage,
  Login,
  Dashboard,
  Opportunities,
  OpportunityDetail,
  Proposals,
  ProposalEditor,
  QualityCheck,
} from '@/pages';

// Protected Route wrapper
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useUserStore();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public Routes */}
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<Login />} />

        {/* Protected Dashboard Routes */}
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <DashboardLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Dashboard />} />
        </Route>

        {/* Protected Opportunities Routes */}
        <Route
          path="/opportunities"
          element={
            <ProtectedRoute>
              <DashboardLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Opportunities />} />
          <Route path=":id" element={<OpportunityDetail />} />
        </Route>

        {/* Protected Proposals Routes */}
        <Route
          path="/proposals"
          element={
            <ProtectedRoute>
              <DashboardLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Proposals />} />
          <Route path=":id" element={<ProposalEditor />} />
          <Route path=":id/qc" element={<QualityCheck />} />
        </Route>

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
