import { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import styles from './Login.module.css'

const GithubIcon = () => (
  <svg viewBox="0 0 16 16" fill="currentColor" width="18" height="18">
    <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38
      0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13
      -.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66
      .07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15
      -.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0
      1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82
      1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01
      1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/>
  </svg>
)

const EyeIcon = ({ off }) => off ? (
  <svg viewBox="0 0 16 16" fill="currentColor" width="15" height="15">
    <path d="M10.79 12.912l-1.614-1.615a3.5 3.5 0 0 1-4.474-4.474L3.087 5.208C1.595 6.178.5 7.584.5 8c.793 2.2 3.355 5.5 7.5 5.5.8 0 1.568-.12 2.29-.338zM5.21 3.088A9.817 9.817 0 0 1 8 2.5c4.145 0 6.707 3.3 7.5 5.5-.34.944-1.005 2.05-1.987 3.012L5.21 3.088zm4.49 4.49a2 2 0 0 0-2.19-2.19l2.19 2.19zm-7.344-7.344L1.293.793 0 2.086l14 14 1.293-1.293L2.356.234z"/>
  </svg>
) : (
  <svg viewBox="0 0 16 16" fill="currentColor" width="15" height="15">
    <path d="M16 8s-3-5.5-8-5.5S0 8 0 8s3 5.5 8 5.5S16 8 16 8zM1.173 8a13.133 13.133 0 0 1 1.66-2.043C4.12 4.668 5.88 3.5 8 3.5c2.12 0 3.879 1.168 5.168 2.457A13.133 13.133 0 0 1 14.828 8c-.058.087-.122.183-.195.288-.335.48-.83 1.12-1.465 1.755C11.879 11.332 10.119 12.5 8 12.5c-2.12 0-3.879-1.168-5.168-2.457A13.134 13.134 0 0 1 1.172 8z"/>
    <path d="M8 5.5a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5zM4.5 8a3.5 3.5 0 1 1 7 0 3.5 3.5 0 0 1-7 0z"/>
  </svg>
)

export default function Login() {
  const [email,    setEmail]    = useState('')
  const [password, setPassword] = useState('')
  const [showPw,   setShowPw]   = useState(false)
  const navigate  = useNavigate()
  const location  = useLocation()
  const { login, loading, error, clearError } = useAuth()

  // Redirect back to where the user came from, or home
  const from = location.state?.from || '/'

  const handleSubmit = async (e) => {
    e.preventDefault()
    clearError()
    const ok = await login(email, password)
    if (ok) navigate(from, { replace: true })
  }

  return (
    <div className={styles.page}>

      {/* Background glow */}
      <div className={styles.glow} />

      <div className={styles.card}>

        {/* Brand */}
        <div className={styles.brand}>
          <div className={styles.brandIcon}><GithubIcon /></div>
          <span className={styles.brandName}>DevProfile AI</span>
        </div>

        <div className={styles.heading}>
          <h1 className={styles.title}>Welcome back</h1>
          <p className={styles.sub}>Sign in to your account to continue</p>
        </div>

        {/* Form */}
        <form className={styles.form} onSubmit={handleSubmit} noValidate>

          <div className={styles.field}>
            <label className={styles.label} htmlFor="email">Email address</label>
            <input
              id="email"
              className={styles.input}
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={e => { setEmail(e.target.value); clearError() }}
              required
              autoFocus
              autoComplete="email"
            />
          </div>

          <div className={styles.field}>
            <div className={styles.labelRow}>
              <label className={styles.label} htmlFor="password">Password</label>
            </div>
            <div className={styles.inputWrap}>
              <input
                id="password"
                className={styles.input}
                type={showPw ? 'text' : 'password'}
                placeholder="Your password"
                value={password}
                onChange={e => { setPassword(e.target.value); clearError() }}
                required
                autoComplete="current-password"
              />
              <button
                type="button"
                className={styles.eyeBtn}
                onClick={() => setShowPw(v => !v)}
                tabIndex={-1}
                aria-label={showPw ? 'Hide password' : 'Show password'}
              >
                <EyeIcon off={showPw} />
              </button>
            </div>
          </div>

          {error && (
            <div className={styles.error} role="alert">
              <svg viewBox="0 0 16 16" fill="currentColor" width="13" height="13">
                <path d="M8 1a7 7 0 1 0 0 14A7 7 0 0 0 8 1zm0 3a.75.75 0 0 1 .75.75v3.5a.75.75 0 0 1-1.5 0v-3.5A.75.75 0 0 1 8 4zm0 8a1 1 0 1 1 0-2 1 1 0 0 1 0 2z"/>
              </svg>
              {error}
            </div>
          )}

          <button className={styles.btn} type="submit" disabled={loading || !email || !password}>
            {loading ? (
              <span className={styles.spinner} />
            ) : (
              <>
                Sign In
                <svg viewBox="0 0 16 16" fill="currentColor" width="13" height="13">
                  <path d="M8.22 2.97a.75.75 0 0 1 1.06 0l4.25 4.25a.75.75 0 0 1 0 1.06l-4.25 4.25a.75.75 0 0 1-1.042-.018.751.751 0 0 1-.018-1.042l2.97-2.97H3.75a.75.75 0 0 1 0-1.5h7.44L8.22 4.03a.75.75 0 0 1 0-1.06Z"/>
                </svg>
              </>
            )}
          </button>
        </form>

        {/* Divider */}
        <div className={styles.divider}><span>or</span></div>

        {/* Footer links */}
        <p className={styles.footer}>
          Don't have an account?{' '}
          <Link to="/signup" className={styles.link}>Create one free</Link>
        </p>

        <button className={styles.skip} onClick={() => navigate('/')}>
          Continue without account
        </button>

      </div>
    </div>
  )
}
