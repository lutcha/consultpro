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
  NewOpportunity,
  Proposals,
  NewProposal,
  ProposalEditor,
  QualityCheck,
  Settings,
  Projects,
  ProjectDetail,
  NewProject,
  Consultants,
  ScrapingPage,
  TeamsPage,
  CurriculumPage,
  Analytics,
  AcceptInvitation,
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
        <Route path="/accept-invitation/:token" element={<AcceptInvitation />} />

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
          <Route path="new" element={<NewOpportunity />} />
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
          <Route path="new" element={<NewProposal />} />
          <Route path=":id" element={<ProposalEditor />} />
          <Route path=":id/qc" element={<QualityCheck />} />
        </Route>

        {/* Projects */}
        <Route
          path="/projects"
          element={
            <ProtectedRoute>
              <DashboardLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Projects />} />
          <Route path="new" element={<NewProject />} />
          <Route path=":id" element={<ProjectDetail />} />
        </Route>

        {/* Consultants */}
        <Route
          path="/consultants"
          element={
            <ProtectedRoute>
              <DashboardLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Consultants />} />
        </Route>

        {/* Teams */}
        <Route
          path="/teams"
          element={
            <ProtectedRoute>
              <DashboardLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<TeamsPage />} />
        </Route>

        {/* Curriculum */}
        <Route
          path="/curriculum"
          element={
            <ProtectedRoute>
              <DashboardLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<CurriculumPage />} />
        </Route>

        {/* Scraping */}
        <Route
          path="/scraping"
          element={
            <ProtectedRoute>
              <DashboardLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<ScrapingPage />} />
        </Route>

        {/* Analytics */}
        <Route
          path="/analytics"
          element={
            <ProtectedRoute>
              <DashboardLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Analytics />} />
        </Route>

        {/* Settings */}
        <Route
          path="/settings"
          element={
            <ProtectedRoute>
              <DashboardLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Settings />} />
        </Route>

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
