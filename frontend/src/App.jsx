import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './hooks/useAuth'
import Home      from './pages/Home.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Login     from './pages/Login.jsx'
import Signup    from './pages/Signup.jsx'

// Redirect already-logged-in users away from auth pages
function GuestRoute({ children }) {
  const { isLoggedIn, initializing } = useAuth()
  if (initializing) return null
  return isLoggedIn ? <Navigate to="/" replace /> : children
}

export default function App() {
  return (
    <Routes>
      <Route path="/"          element={<Home />} />
      <Route path="/dashboard" element={<Dashboard />} />

      <Route path="/login"  element={<GuestRoute><Login  /></GuestRoute>} />
      <Route path="/signup" element={<GuestRoute><Signup /></GuestRoute>} />

      {/* Backward compat: /auth → /login */}
      <Route path="/auth" element={<Navigate to="/login" replace />} />
    </Routes>
  )
}
