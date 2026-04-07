import { useState, useEffect } from 'react'
import styles from './Loader.module.css'

const STEPS = [
  'Fetching GitHub profile...',
  'Collecting repository data...',
  'Building feature vector...',
  'Running ML models...',
  'Generating AI insights...',
]

export function Spinner({ size = 40 }) {
  return (
    <div
      className={styles.spinner}
      style={{ width: size, height: size, borderWidth: size / 10 }}
    />
  )
}

export function FullPageLoader({ message }) {
  const [step, setStep] = useState(0)

  useEffect(() => {
    const id = setInterval(() => setStep(s => (s + 1) % STEPS.length), 1800)
    return () => clearInterval(id)
  }, [])

  return (
    <div className={styles.fullPage}>
      <Spinner size={52} />
      <p className={styles.message}>{message}</p>
      <div className={styles.steps}>
        {STEPS.map((s, i) => (
          <div
            key={i}
            className={`${styles.step} ${i === step ? styles.stepActive : ''} ${i < step ? styles.stepDone : ''}`}
          >
            <span className={styles.stepDot} />
            <span>{s}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

export function SkeletonBlock({ height = 120 }) {
  return <div className={styles.skeleton} style={{ height }} />
}

export function SkeletonDashboard() {
  return (
    <div className={styles.skGrid}>
      <div className={styles.skRow2}>
        <SkeletonBlock height={180} />
        <SkeletonBlock height={180} />
      </div>
      <div className={styles.skRow2}>
        <SkeletonBlock height={260} />
        <SkeletonBlock height={260} />
      </div>
      <SkeletonBlock height={320} />
    </div>
  )
}
