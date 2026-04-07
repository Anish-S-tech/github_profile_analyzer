import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import styles from './Home.module.css'

const PLACEHOLDERS = ['torvalds', 'karpathy', 'gaearon', 'sindresorhus', 'addyosmani']
const FEATURES = [
  { label: 'Impact Score',      desc: 'ML-predicted influence level' },
  { label: 'Skill Detection',   desc: 'Language-based developer type' },
  { label: 'Contribution Style',desc: 'How you build and ship' },
  { label: 'Maturity Score',    desc: 'Project depth and consistency' },
  { label: 'AI Insights',       desc: 'Ollama-powered career advice' },
]

function useTypewriter(words, speed = 80, pause = 1800) {
  const [text, setText] = useState('')
  const [wordIdx, setWordIdx] = useState(0)
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    const word = words[wordIdx % words.length]
    const timeout = setTimeout(() => {
      if (!deleting) {
        setText(word.slice(0, text.length + 1))
        if (text.length + 1 === word.length) setTimeout(() => setDeleting(true), pause)
      } else {
        setText(word.slice(0, text.length - 1))
        if (text.length - 1 === 0) { setDeleting(false); setWordIdx(i => i + 1) }
      }
    }, deleting ? speed / 2 : speed)
    return () => clearTimeout(timeout)
  }, [text, deleting, wordIdx])

  return text
}

export default function Home() {
  const [username, setUsername] = useState('')
  const [focused,  setFocused]  = useState(false)
  const navigate  = useNavigate()
  const inputRef  = useRef(null)
  const placeholder = useTypewriter(PLACEHOLDERS)

  // Press / to focus input
  useEffect(() => {
    const handler = (e) => {
      if (e.key === '/' && document.activeElement !== inputRef.current) {
        e.preventDefault()
        inputRef.current?.focus()
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [])

  const handleSubmit = (e) => {
    e.preventDefault()
    const u = username.trim()
    if (u) navigate(`/dashboard?user=${encodeURIComponent(u)}`)
  }

  return (
    <div className={styles.page}>
      <div className={styles.hero}>

        {/* Logo */}
        <div className={styles.logo}>
          <svg viewBox="0 0 16 16" fill="currentColor" className={styles.logoSvg}>
            <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38
              0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13
              -.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66
              .07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15
              -.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0
              1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82
              1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01
              1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/>
          </svg>
          <span>GitHub Intelligence</span>
        </div>

        <h1 className={styles.headline}>
          Understand any developer<br />
          <span className={styles.accent}>with ML + AI</span>
        </h1>

        <p className={styles.sub}>
          Enter a GitHub username and get an instant analysis of impact,
          skills, contribution style, and AI-generated career insights.
        </p>

        {/* Search form */}
        <form className={styles.form} onSubmit={handleSubmit}>
          <div className={`${styles.inputWrapper} ${focused ? styles.inputFocused : ''}`}>
            <span className={styles.at}>@</span>
            <input
              ref={inputRef}
              className={styles.input}
              type="text"
              placeholder={placeholder || 'Enter GitHub username'}
              value={username}
              onChange={e => setUsername(e.target.value)}
              onFocus={() => setFocused(true)}
              onBlur={() => setFocused(false)}
              autoComplete="off"
              spellCheck="false"
            />
            {!focused && !username && (
              <kbd className={styles.kbd}>/</kbd>
            )}
          </div>
          <button className={styles.btn} type="submit" disabled={!username.trim()}>
            Analyze
            <svg viewBox="0 0 16 16" fill="currentColor" width="14" height="14">
              <path d="M8.22 2.97a.75.75 0 0 1 1.06 0l4.25 4.25a.75.75 0 0 1 0 1.06l-4.25 4.25a.75.75 0 0 1-1.042-.018.751.751 0 0 1-.018-1.042l2.97-2.97H3.75a.75.75 0 0 1 0-1.5h7.44L8.22 4.03a.75.75 0 0 1 0-1.06Z"/>
            </svg>
          </button>
        </form>

        {/* Quick examples */}
        <div className={styles.examples}>
          <span className={styles.exLabel}>Try:</span>
          {['torvalds', 'karpathy', 'gaearon', 'sindresorhus'].map(u => (
            <button
              key={u}
              className={styles.exBtn}
              onClick={() => navigate(`/dashboard?user=${u}`)}
            >
              {u}
            </button>
          ))}
        </div>

        {/* Feature grid */}
        <div className={styles.features}>
          {FEATURES.map((f, i) => (
            <div key={i} className={styles.feature} style={{ animationDelay: `${i * 0.08}s` }}>
              <span className={styles.featureLabel}>{f.label}</span>
              <span className={styles.featureDesc}>{f.desc}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
