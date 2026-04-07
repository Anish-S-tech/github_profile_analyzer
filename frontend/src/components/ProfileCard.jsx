import { useEffect, useRef, useState } from 'react'
import styles from './ProfileCard.module.css'

function useCountUp(target, duration = 1200) {
  const [value, setValue] = useState(0)
  useEffect(() => {
    if (target === 0) return
    let start = 0
    const step = target / (duration / 16)
    const id = setInterval(() => {
      start += step
      if (start >= target) { setValue(target); clearInterval(id) }
      else setValue(Math.floor(start))
    }, 16)
    return () => clearInterval(id)
  }, [target])
  return value
}

function StatItem({ label, value }) {
  const animated = useCountUp(value)
  return (
    <div className={styles.stat}>
      <span className={styles.statValue}>{animated.toLocaleString()}</span>
      <span className={styles.statLabel}>{label}</span>
    </div>
  )
}

export default function ProfileCard({ profile, username }) {
  const years = (profile.account_age_days / 365).toFixed(1)

  return (
    <div className={styles.card}>
      <div className={styles.header}>
        <div className={styles.avatarWrapper}>
          <img
            className={styles.avatar}
            src={`https://github.com/${username}.png`}
            alt={username}
            onError={e => { e.target.src = 'https://github.com/ghost.png' }}
          />
          <div className={styles.avatarGlow} />
        </div>
        <div className={styles.info}>
          <h2 className={styles.username}>
            <a href={`https://github.com/${username}`} target="_blank" rel="noreferrer">
              @{username}
            </a>
          </h2>
          <p className={styles.age}>Member for {years} years</p>
          <a
            className={styles.ghLink}
            href={`https://github.com/${username}`}
            target="_blank"
            rel="noreferrer"
          >
            View on GitHub
            <svg viewBox="0 0 16 16" fill="currentColor" width="12" height="12">
              <path d="M3.75 2h3.5a.75.75 0 0 1 0 1.5h-3.5a.25.25 0 0 0-.25.25v8.5c0 .138.112.25.25.25h8.5a.25.25 0 0 0 .25-.25v-3.5a.75.75 0 0 1 1.5 0v3.5A1.75 1.75 0 0 1 12.25 14h-8.5A1.75 1.75 0 0 1 2 12.25v-8.5C2 2.784 2.784 2 3.75 2Zm6.854-1h4.146a.25.25 0 0 1 .25.25v4.146a.25.25 0 0 1-.427.177L13.03 4.03 9.28 7.78a.751.751 0 0 1-1.042-.018.751.751 0 0 1-.018-1.042l3.75-3.75-1.543-1.543A.25.25 0 0 1 10.604 1Z"/>
            </svg>
          </a>
        </div>
      </div>

      <div className={styles.divider} />

      <div className={styles.stats}>
        <StatItem label="Followers"  value={profile.followers}   />
        <StatItem label="Repos"      value={profile.repo_count}  />
        <StatItem label="Stars"      value={profile.total_stars} />
        <StatItem label="Forks"      value={profile.total_forks} />
      </div>
    </div>
  )
}
