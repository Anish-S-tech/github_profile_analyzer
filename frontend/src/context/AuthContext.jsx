import { createContext, useContext, useState, useCallback, useEffect } from 'react'
import {
  apiLogin, apiRegister, apiLogout, apiMe,
  getToken, setToken, setUser, clearToken, clearUser, getUser,
} from '../api/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user,         setUserState]  = useState(() => getUser())
  const [loading,      setLoading]    = useState(false)
  const [error,        setError]      = useState(null)
  const [initializing, setInitializing] = useState(!!getToken())

  // On mount: verify stored JWT is still valid with the backend
  useEffect(() => {
    const token = getToken()
    if (!token) { setInitializing(false); return }
    apiMe()
      .then(u  => { setUser(u); setUserState(u) })
      .catch(() => { clearToken(); clearUser(); setUserState(null) })
      .finally(() => setInitializing(false))
  }, [])

  const login = useCallback(async (email, password) => {
    setLoading(true); setError(null)
    try {
      const data = await apiLogin(email, password)
      setToken(data.access_token)
      setUser(data.user)
      setUserState(data.user)
      return true
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Login failed')
      return false
    } finally { setLoading(false) }
  }, [])

  const register = useCallback(async (email, password) => {
    setLoading(true); setError(null)
    try {
      const data = await apiRegister(email, password)
      if (data.access_token) {
        setToken(data.access_token)
        setUser(data.user)
        setUserState(data.user)
      }
      return true
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Registration failed')
      return false
    } finally { setLoading(false) }
  }, [])

  const logout = useCallback(async () => {
    try { await apiLogout() } catch {}
    clearToken(); clearUser(); setUserState(null)
  }, [])

  const clearError = useCallback(() => setError(null), [])

  return (
    <AuthContext.Provider value={{
      user, loading, error, initializing,
      login, register, logout, clearError,
      isLoggedIn: !!user,
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}
