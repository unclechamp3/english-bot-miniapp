import './StatsCard.css'

function StatsCard({ icon, title, value, subtitle, trend }) {
  return (
    <div className="stats-card">
      <div className="stats-card-icon">{icon}</div>
      <div className="stats-card-content">
        <div className="stats-card-title">{title}</div>
        <div className="stats-card-value">
          {value}
          {trend && (
            <span className={`stats-card-trend ${trend > 0 ? 'up' : 'down'}`}>
              {trend > 0 ? '↑' : '↓'} {Math.abs(trend)}
            </span>
          )}
        </div>
        {subtitle && <div className="stats-card-subtitle">{subtitle}</div>}
      </div>
    </div>
  )
}

export default StatsCard

