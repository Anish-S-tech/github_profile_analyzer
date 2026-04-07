import { useState } from 'react'
import {
  PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer, Sector,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, LabelList,
} from 'recharts'
import styles from './Charts.module.css'

const COLORS = ['#58a6ff','#3fb950','#bc8cff','#f0883e','#d29922','#f85149','#79c0ff','#56d364']

const TOOLTIP_STYLE = {
  background: '#1c2128',
  border: '1px solid #30363d',
  borderRadius: 8,
  fontSize: 13,
  color: '#e6edf3',
}

// Active pie slice that expands on hover
function ActiveShape(props) {
  const { cx, cy, innerRadius, outerRadius, startAngle, endAngle, fill, payload, percent } = props
  return (
    <g>
      <text x={cx} y={cy - 10} textAnchor="middle" fill="#e6edf3" fontSize={15} fontWeight={700}>
        {payload.name}
      </text>
      <text x={cx} y={cy + 14} textAnchor="middle" fill="#8b949e" fontSize={13}>
        {`${(percent * 100).toFixed(1)}%`}
      </text>
      <Sector cx={cx} cy={cy} innerRadius={innerRadius} outerRadius={outerRadius + 8}
        startAngle={startAngle} endAngle={endAngle} fill={fill} />
      <Sector cx={cx} cy={cy} innerRadius={outerRadius + 12} outerRadius={outerRadius + 16}
        startAngle={startAngle} endAngle={endAngle} fill={fill} />
    </g>
  )
}

export function LanguageChart({ languages }) {
  const [activeIndex, setActiveIndex] = useState(0)

  if (!languages || Object.keys(languages).length === 0) {
    return (
      <div className={styles.card}>
        <h3 className={styles.title}>Language Distribution</h3>
        <div className={styles.empty}>No language data available.</div>
      </div>
    )
  }

  const data = Object.entries(languages).map(([name, value]) => ({
    name,
    value: Math.round(value * 100),
  }))

  return (
    <div className={styles.card}>
      <h3 className={styles.title}>Language Distribution</h3>
      <ResponsiveContainer width="100%" height={260}>
        <PieChart>
          <Pie
            activeIndex={activeIndex}
            activeShape={ActiveShape}
            data={data}
            cx="50%" cy="50%"
            innerRadius={60} outerRadius={95}
            paddingAngle={2}
            dataKey="value"
            onMouseEnter={(_, i) => setActiveIndex(i)}
          >
            {data.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} stroke="transparent" />
            ))}
          </Pie>
          <Legend
            iconType="circle"
            iconSize={8}
            formatter={(v) => <span style={{ color: '#8b949e', fontSize: 12 }}>{v}</span>}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}

export function StarsChart({ profile }) {
  const data = [
    { name: 'Stars',     value: profile.total_stars, color: '#58a6ff' },
    { name: 'Forks',     value: profile.total_forks, color: '#3fb950' },
    { name: 'Repos',     value: profile.repo_count,  color: '#bc8cff' },
    { name: 'Followers', value: profile.followers,   color: '#f0883e' },
  ]

  return (
    <div className={styles.card}>
      <h3 className={styles.title}>Profile Stats</h3>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={data} margin={{ top: 20, right: 16, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#21262d" vertical={false} />
          <XAxis
            dataKey="name"
            tick={{ fill: '#8b949e', fontSize: 12 }}
            axisLine={false} tickLine={false}
          />
          <YAxis
            tick={{ fill: '#8b949e', fontSize: 11 }}
            axisLine={false} tickLine={false}
            width={55}
          />
          <Tooltip
            contentStyle={TOOLTIP_STYLE}
            cursor={{ fill: 'rgba(88,166,255,0.06)', radius: 4 }}
            formatter={(v) => [v.toLocaleString(), '']}
          />
          <Bar dataKey="value" radius={[6, 6, 0, 0]} maxBarSize={56}>
            {data.map((d, i) => (
              <Cell key={i} fill={d.color} />
            ))}
            <LabelList
              dataKey="value"
              position="top"
              formatter={(v) => v > 999 ? `${(v/1000).toFixed(1)}k` : v}
              style={{ fill: '#8b949e', fontSize: 11 }}
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
