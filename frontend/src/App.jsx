import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './auth/useAuth.js'
import ProtectedRoute from './auth/ProtectedRoute.jsx'
import LoginPage from './pages/LoginPage.jsx'
import AdminDashboard from './pages/admin/AdminDashboard.jsx'
import CandidateStatusPage from './pages/candidate/CandidateStatusPage.jsx'
import AssignedCandidatesPage from './pages/interviewer/AssignedCandidatesPage.jsx'

export default function App() {
  const { auth, logout } = useAuth()

  return (
    <div className="app-shell">
      {auth && (
        <nav className="app-nav" aria-label="Application navigation">
          <div className="app-brand"><span className="brand-mark-small">SH</span><span>SmartHire</span></div>
          <div className="session-actions">
            <div className="session-identity">
              <span className="session-avatar">{auth.username.slice(0, 1).toUpperCase()}</span>
              <span><strong>{auth.username}</strong><small>{auth.role}</small></span>
            </div>
            <button className="logout-button" type="button" onClick={logout} aria-label="Log out">
              <span aria-hidden="true">-&gt;</span> Log out
            </button>
          </div>
        </nav>
      )}

      <Routes>
        <Route path="/login" element={<LoginPage />} />

        <Route
          path="/admin"
          element={
            <ProtectedRoute role="admin">
              <AdminDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/candidate"
          element={
            <ProtectedRoute role="candidate">
              <CandidateStatusPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/interviewer"
          element={
            <ProtectedRoute role="interviewer">
              <AssignedCandidatesPage />
            </ProtectedRoute>
          }
        />

        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </div>
  )
}
