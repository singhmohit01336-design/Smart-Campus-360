import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import DashboardLayout from './layouts/DashboardLayout';

// Auth Pages
import Login from './pages/auth/Login';
import Register from './pages/auth/Register';

// Main App Pages
import RoleDashboard from './pages/dashboards/RoleDashboard';
import TicketListPage from './pages/tickets/TicketListPage';
import TicketCreatePage from './pages/tickets/TicketCreatePage';
import TicketDetailPage from './pages/tickets/TicketDetailPage';
import KnowledgeBasePage from './pages/knowledge-base/KnowledgeBasePage';
import AnalyticsPage from './pages/analytics/AnalyticsPage';
import SlaMonitorPage from './pages/sla/SlaMonitorPage';
import QRScannerPage from './pages/qr/QRScannerPage';

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public Authentication Routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* Protected Routes inside App Layout */}
          <Route
            element={
              <ProtectedRoute>
                <DashboardLayout />
              </ProtectedRoute>
            }
          >
            {/* Role Dispatcher Dashboard */}
            <Route path="/" element={<RoleDashboard />} />

            {/* Helpdesk & Complaints */}
            <Route path="/tickets" element={<TicketListPage />} />
            <Route path="/tickets/new" element={<TicketCreatePage />} />
            <Route path="/tickets/:id" element={<TicketDetailPage />} />

            {/* Knowledge Base */}
            <Route path="/knowledge-base" element={<KnowledgeBasePage />} />

            {/* Classroom QR Scanning */}
            <Route path="/qr" element={<QRScannerPage />} />

            {/* Admin / Superadmin Only Intelligence */}
            <Route
              path="/analytics"
              element={
                <ProtectedRoute allowedRoles={['admin', 'superadmin']}>
                  <AnalyticsPage />
                </ProtectedRoute>
              }
            />

            <Route
              path="/sla"
              element={
                <ProtectedRoute allowedRoles={['admin', 'superadmin']}>
                  <SlaMonitorPage />
                </ProtectedRoute>
              }
            />
          </Route>

          {/* Catch-all fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
