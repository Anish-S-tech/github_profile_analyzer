import { useState } from 'react'
import styles from './InsightsPanel.module.css'

const TABS = ['Summary', 'Strengths', 'Weaknesses', 'Suggestions', 'Growth Plan']

function TabContent({ tab, insights }) {
  if (tab === 'Summary') {
    return (
      <div className={styles.summary}>
        <p>{insights.summary}</p>
      </div>
    )
  }

  if (tab === 'Strengths') {
    return (
      <ul className={styles.list}>
        {(insights.strengths || []).map((item, i) => (
          <li key={i} className={`${styles.listItem} ${styles.green}`}>
            <span className={styles.dot} style={{ background: 'var(--green)' }} />
            {item}
          </li>
        ))}
      </ul>
    )
  }

  if (tab === 'Weaknesses') {
    return (
      <ul className={styles.list}>
        {(insights.weaknesses || []).map((item, i) => (
          <li key={i} className={`${styles.listItem} ${styles.yellow}`}>
            <span className={styles.dot} style={{ background: 'var(--yellow)' }} />
            {item}
          </li>
        ))}
      </ul>
    )
  }

  if (tab === 'Suggestions') {
    return (
      <div className={styles.suggestions}>
        {(insights.suggestions || []).map((s, i) => (
          <div key={i} className={styles.suggestion}>
            <span className={styles.suggNum}>{i + 1}</span>
            <span>{s}</span>
          </div>
        ))}
      </div>
    )
  }

  if (tab === 'Growth Plan') {
    return (
      <div className={styles.growthPlan}>
        <div className={styles.growthHeader}>30-Day Growth Plan</div>
        <p>{insights.growth_plan || 'No growth plan generated.'}</p>
      </div>
    )
  }

  return null
}

export default function InsightsPanel({ insights }) {
  const [activeTab, setActiveTab] = useState('Summary')

  if (!insights) {
    return (
      <div className={styles.card}>
        <h3 className={styles.title}>AI Insights</h3>
        <div className={styles.noLlm}>
          <div className={styles.noLlmIcon}>
            <svg viewBox="0 0 16 16" fill="currentColor" width="24" height="24">
              <path d="M8 0a8 8 0 1 1 0 16A8 8 0 0 1 8 0ZM1.5 8a6.5 6.5 0 1 0 13 0 6.5 6.5 0 0 0-13 0Zm7-3.25v2.992l2.028.812a.75.75 0 0 1-.557 1.392l-2.5-1A.751.751 0 0 1 7 8.25v-3.5a.75.75 0 0 1 1.5 0Z"/>
            </svg>
          </div>
          <p>LLM insights not available.</p>
          <p className={styles.noLlmSub}>Make sure Ollama is running and re-analyze.</p>
        </div>
      </div>
    )
  }

  return (
    <div className={styles.card}>
      <div className={styles.cardHeader}>
        <h3 className={styles.title}>AI Insights</h3>
        <span className={styles.badge}>Powered by Ollama</span>
      </div>

      {/* Tabs */}
      <div className={styles.tabs}>
        {TABS.map(tab => (
          <button
            key={tab}
            className={`${styles.tab} ${activeTab === tab ? styles.tabActive : ''}`}
            onClick={() => setActiveTab(tab)}
          >
            {tab}
            {tab === 'Strengths'   && insights.strengths?.length   > 0 && (
              <span className={styles.tabCount} style={{ background: 'var(--green)' }}>
                {insights.strengths.length}
              </span>
            )}
            {tab === 'Weaknesses'  && insights.weaknesses?.length  > 0 && (
              <span className={styles.tabCount} style={{ background: 'var(--yellow)' }}>
                {insights.weaknesses.length}
              </span>
            )}
            {tab === 'Suggestions' && insights.suggestions?.length > 0 && (
              <span className={styles.tabCount} style={{ background: 'var(--accent)' }}>
                {insights.suggestions.length}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className={styles.content}>
        <TabContent tab={activeTab} insights={insights} />
      </div>
    </div>
  )
}
