import { useEffect, useState } from 'react'
import styles from './MetricsCard.module.css'

const LEVEL_COLOR = {
  'Explorer':    'var(--red)',
  'Growing':     'var(--yellow)',
  'Advanced':    'var(--accent)',
  'High Impact': 'var(--green)',
}

const MATURITY_COLOR = {
  'Early Stage':  'var(--red)',
  'Developing':   'var(--yellow)',
  'Experienced':  'var(--accent)',
  'Expert':       'var(--green)',
}

function useAnimatedValue(target, duration = 1000) {
  const [val, setVal] = useState(0)
  useEffect(() => {
    let start = 0
    const step = target / (duration / 16)
    const id = setInterval(() => {
      start += step
      if (start >= target) { setVal(target); clearInterval(id) }
      else setVal(parseFloat(start.toFixed(2)))
    }, 16)
    return () => clearInterval(id)
  }, [target])
  return val
}

function ImpactGauge({ score, level }) {
  const animated = useAnimatedValue(score)
  const r     = 54
  const circ  = 2 * Math.PI * r
  const prog  = (animated / 100) * circ
  const color = LEVEL_COLOR[level] || 'var(--accent)'

  return (
    <div className={styles.gaugeWrapper}>
      <svg width="136" height="136" viewBox="0 0 136 136">
        {/* Track */}
        <circle cx="68" cy="68" r={r} fill="none" stroke="var(--surface3)" strokeWidth="10" />
        {/* Progress */}
        <circle
          cx="68" cy="68" r={r}
          fill="none"
          stroke={color}
          strokeWidth="10"
          strokeDasharray={`${prog} ${circ}`}
          strokeLinecap="round"
          transform="rotate(-90 68 68)"
        />
        {/* Glow */}
        <circle
          cx="68" cy="68" r={r}
          fill="none"
          stroke={color}
          strokeWidth="2"
          strokeDasharray={`${prog} ${circ}`}
          strokeLinecap="round"
          transform="rotate(-90 68 68)"
          opacity="0.3"
          filter="blur(4px)"
        />
      </svg>
      <div className={styles.gaugeCenter}>
        <span className={styles.gaugeScore} style={{ color }}>{animated.toFixed(0)}</span>
        <span className={styles.gaugeDenom}>/100</span>
      </div>
      <span className={styles.gaugeLevel} style={{ color }}>{level}</span>
    </div>
  )
}

function Badge({ label, value, color }) {
  return (
    <div className={styles.badge} style={{ '--badge-color': color }}>
      <div className={styles.badgeAccent} />
      <div className={styles.badgeContent}>
        <span className={styles.badgeLabel}>{label}</span>
        <span className={styles.badgeValue}>{value}</span>
      </div>
    </div>
  )
}

function MaturityBar({ score, level }) {
  const animated = useAnimatedValue(score)
  const color = MATURITY_COLOR[level] || 'var(--accent)'

  return (
    <div className={styles.maturity}>
      <div className={styles.maturityHeader}>
        <span className={styles.maturityLabel}>Maturity Score</span>
        <span className={styles.maturityValue} style={{ color }}>
          {animated.toFixed(0)} / 100
          <span className={styles.maturityLevel}>{level}</span>
        </span>
      </div>
      <div className={styles.barTrack}>
        <div
          className={styles.barFill}
          style={{ width: `${animated}%`, background: color }}
        />
        <div
          className={styles.barGlow}
          style={{ width: `${animated}%`, background: color }}
        />
      </div>
    </div>
  )
}

export default function MetricsCard({ metrics }) {
  return (
    <div className={styles.card}>
      <h3 className={styles.title}>ML Analysis</h3>

      <div className={styles.top}>
        <ImpactGauge score={metrics.impact_score} level={metrics.impact_level} />
        <div className={styles.badges}>
          <Badge label="Skill Type"         value={metrics.skill_type}                  color="var(--purple)" />
          <Badge label="Contribution Style" value={metrics.contribution_type}           color="var(--orange)" />
          <Badge label="Top Language"       value={metrics.top_language || 'Unknown'}   color="var(--accent)" />
        </div>
      </div>

      <MaturityBar score={metrics.maturity_score} level={metrics.maturity_level} />
    </div>
  )
}
