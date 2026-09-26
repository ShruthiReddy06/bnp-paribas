import { Navigate } from 'react-router-dom'
import { useAuth } from './useAuth.js'

export default function ProtectedRoute({ role, children }) {
  const { auth } = useAuth()

  if (!auth) return <Navigate to="/login" replace />
  if (role && auth.role !== role) return <Navigate to="/login" replace />

  return children
}
