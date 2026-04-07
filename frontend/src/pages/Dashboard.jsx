import { useEffect, useState } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { useAnalysis } from '../hooks/useAnalysis'
import ProfileCard   from '../components/ProfileCard.jsx'
import MetricsCard   from '../components/MetricsCard.jsx'
import { LanguageChart, StarsChart } from '../components/Charts.jsx'
import InsightsPanel from '../components/InsightsPanel.jsx'
import { FullPageLoader, SkeletonDashboard } from '../components/Loader.jsx'
import styles from './Dashboard.module.css'

export default function Dashboard() {
  const [params]   = useSearchParams()
  const navigate   = useNavigate()
  const username   = params.get('user') || ''
  const [useLlm, setUseLlm] = useState(true)
  const { data, loading, error, analyze, reset } = useAnalysis()

  useEffect(() => {
    if (username) analyze(username, useLlm)
  }, [username])

  const handleAnalyze = () => analyze(username, useLlm)
  const handleBack    = () => { reset(); navigate('/') }

  return (
    <div className={styles.page}>

      {/* Header */}
      <header className={styles.header}>
        <button className={styles.backBtn} onClick={handleBack}>
          <svg viewBox="0 0 16 16" fill="currentColor" width="14" height="14">
            <path d="M7.78 12.53a.75.75 0 0 1-1.06 0L2.47 8.28a.75.75 0 0 1 0-1.06l4.25-4.25a.751.751 0 0 1 1.042.018.751.751 0 0 1 .018 1.042L4.81 7h7.44a.75.75 0 0 1 0 1.5H4.81l2.97 2.97a.75.75 0 0 1 0 1.06Z"/>
          </svg>
          Back
        </button>

        <div className={styles.headerCenter}>
          {username && (
            <span className={styles.headerUser}>
              <img
                src={`https://github.com/${username}.png`}
                alt=""
                className={styles.headerAvatar}
                onError={e => { e.target.style.display = 'none' }}
              />
              @{username}
            </span>
          )}
        </div>

        <div className={styles.headerRight}>
          {/* LLM toggle */}
          <label className={styles.toggle}>
            <span className={styles.toggleLabel}>AI Insights</span>
            <div
              className={`${styles.toggleSwitch} ${useLlm ? styles.toggleOn : ''}`}
              onClick={() => setUseLlm(v => !v)}
            >
              <div className={styles.toggleThumb} />
            </div>
          </label>

          {data && (
            <button className={styles.reanalyzeBtn} onClick={handleAnalyze} disabled={loading}>
              {loading ? 'Analyzing...' : 'Re-analyze'}
            </button>
          )}
        </div>
      </header>

      {/* Loading */}
      {loading && !data && <FullPageLoader message={`Analyzing @${username}`} />}
      {loading &&  data && <SkeletonDashboard />}

      {/* Error */}
      {error && !loading && (
        <div className={styles.errorBox}>
          <svg viewBox="0 0 16 16" fill="currentColor" width="16" height="16">
            <path d="M6.457 1.047c.659-1.234 2.427-1.234 3.086 0l6.082 11.378A1.75 1.75 0 0 1 14.082 15H1.918a1.75 1.75 0 0 1-1.543-2.575Zm1.763.707a.25.25 0 0 0-.44 0L1.698 13.132a.25.25 0 0 0 .22.368h12.164a.25.25 0 0 0 .22-.368Zm.53 3.996v2.5a.75.75 0 0 1-1.5 0v-2.5a.75.75 0 0 1 1.5 0ZM9 11a1 1 0 1 1-2 0 1 1 0 0 1 2 0Z"/>
          </svg>
          {error}
          <button className={styles.retryBtn} onClick={handleAnalyze}>Retry</button>
        </div>
      )}

      {/* Results */}
      {data && !loading && (
        <div className={styles.grid}>

          <div className={styles.row2}>
            <ProfileCard profile={data.profile} username={data.username} />
            <MetricsCard metrics={data.metrics} />
          </div>

          <div className={styles.row2}>
            <LanguageChart languages={data.languages} />
            <StarsChart    profile={data.profile} />
          </div>

          <InsightsPanel insights={data.insights} />

          {data.warnings?.length > 0 && (
            <div className={styles.warnings}>
              {data.warnings.map((w, i) => (
                <div key={i} className={styles.warning}>{w}</div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
