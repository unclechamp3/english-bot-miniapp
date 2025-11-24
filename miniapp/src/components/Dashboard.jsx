import { useState, useEffect } from 'react'
import StatsCard from './StatsCard'
import Charts from './Charts'
import { getUserAnalytics, getChartData } from '../services/api'
import './Dashboard.css'

function Dashboard({ userId, initData, tg }) {
  const [analytics, setAnalytics] = useState(null)
  const [chartData, setChartData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true)
        setError(null)

        // Fetch analytics and chart data in parallel
        const [analyticsData, charts] = await Promise.all([
          getUserAnalytics(userId, initData),
          getChartData(userId, initData, 7)
        ])

        setAnalytics(analyticsData)
        setChartData(charts)
      } catch (err) {
        console.error('Error fetching data:', err)
        setError(err.message)
        
        // Show error in Telegram
        if (tg) {
          tg.showAlert('Failed to load analytics: ' + err.message)
        }
      } finally {
        setLoading(false)
      }
    }

    if (userId && initData) {
      fetchData()
    }
  }, [userId, initData, tg])

  if (loading) {
    return (
      <div className="dashboard">
        <div className="loading">
          <div className="spinner"></div>
          <p>Loading analytics...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="dashboard">
        <div className="error">
          <h2>Error Loading Data</h2>
          <p>{error}</p>
          <button 
            className="retry-button"
            onClick={() => window.location.reload()}
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  if (!analytics) {
    return (
      <div className="dashboard">
        <div className="no-data">
          <h2>📊 No Data Yet</h2>
          <p>Start practicing English to see your progress here!</p>
        </div>
      </div>
    )
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>📈 Your Progress</h1>
        <p className="dashboard-subtitle">Track your English learning journey</p>
      </div>

      <div className="stats-grid">
        <StatsCard
          icon="💬"
          title="Total Messages"
          value={analytics.total_messages}
          subtitle={`${analytics.voice_messages} voice, ${analytics.text_messages} text`}
          trend={analytics.messages_this_week}
        />

        <StatsCard
          icon="❌"
          title="Grammar Errors"
          value={analytics.total_errors}
          subtitle={`${analytics.error_rate}% error rate`}
        />

        <StatsCard
          icon="🔥"
          title="Practice Streak"
          value={`${analytics.streak} ${analytics.streak === 1 ? 'day' : 'days'}`}
          subtitle={`${analytics.practice_days?.length || 0} days total`}
        />
      </div>

      {chartData && chartData.daily && (
        <Charts 
          dailyData={chartData.daily} 
          errorTypes={chartData.error_types || {}} 
        />
      )}

      <div className="future-features">
        <button className="feature-button disabled" disabled>
          ⭐ Premium
          <span className="badge">Coming Soon</span>
        </button>
        <button className="feature-button disabled" disabled>
          ⚙️ Settings
          <span className="badge">Coming Soon</span>
        </button>
      </div>
    </div>
  )
}

export default Dashboard

