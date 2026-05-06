import axios from 'axios'

const BASE = 'http://localhost:8000'

// ── Auth token helpers ────────────────────────────────────────
export const getToken   = ()  => localStorage.getItem('access_token')
export const setToken   = (t) => localStorage.setItem('access_token', t)
export const clearToken = ()  => localStorage.removeItem('access_token')
export const getUser    = ()  => { try { return JSON.parse(localStorage.getItem('user') || 'null') } catch { return null } }
export const setUser    = (u) => localStorage.setItem('user', JSON.stringify(u))
export const clearUser  = ()  => localStorage.removeItem('user')

const api = axios.create({ baseURL: BASE })

// Auto-attach JWT on every request
api.interceptors.request.use(cfg => {
  const token = getToken()
  if (token) cfg.headers.Authorization = `Bearer ${token}`
  return cfg
})

// On 401: clear stale token and redirect to /login
// Skip redirect if the failing request was itself an auth call
// (prevents redirect loop when login credentials are wrong)
const AUTH_PATHS = ['/auth/login', '/auth/register', '/auth/me']

api.interceptors.response.use(
  res => res,
  err => {
    const url = err.config?.url || ''
    const is401 = err.response?.status === 401
    const isAuthCall = AUTH_PATHS.some(p => url.includes(p))

    if (is401 && !isAuthCall) {
      clearToken(); clearUser()
      if (!window.location.pathname.startsWith('/login') &&
          !window.location.pathname.startsWith('/signup')) {
        window.location.href = '/login'
      }
    }
    return Promise.reject(err)
  }
)

// ── Auth ──────────────────────────────────────────────────────
export const apiRegister = (email, password) =>
  api.post('/auth/register', { email, password }).then(r => r.data)

export const apiLogin = (email, password) =>
  api.post('/auth/login', { email, password }).then(r => r.data)

export const apiLogout = () =>
  api.post('/auth/logout').then(r => r.data)

export const apiMe = () =>
  api.get('/auth/me').then(r => r.data)

// ── Analysis ──────────────────────────────────────────────────
export const analyzeUser = (username, useLlm = true) =>
  api.post('/analyze', { username, use_llm: useLlm }).then(r => r.data)

// ── History ───────────────────────────────────────────────────
export const getGithubHistory = (username, limit = 10) =>
  api.get(`/history/${username}`, { params: { limit } }).then(r => r.data)

export const getMySearches = (limit = 20) =>
  api.get('/my-searches', { params: { limit } }).then(r => r.data)

// ── System ────────────────────────────────────────────────────
export const checkHealth = () =>
  api.get('/health').then(r => r.data)
