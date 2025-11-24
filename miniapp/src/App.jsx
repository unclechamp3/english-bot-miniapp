import { useEffect, useState } from 'react'
import Dashboard from './components/Dashboard'
import './App.css'

function App() {
  const [tg, setTg] = useState(null)
  const [userId, setUserId] = useState(null)
  const [initData, setInitData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    // Initialize Telegram WebApp
    if (window.Telegram && window.Telegram.WebApp) {
      const webapp = window.Telegram.WebApp
      setTg(webapp)
      
      // Expand the WebApp to full height
      webapp.ready()
      webapp.expand()
      
      // Get user data from Telegram
      const user = webapp.initDataUnsafe?.user
      const data = webapp.initData
      
      if (user && user.id) {
        setUserId(user.id)
        setInitData(data)
        console.log('Telegram user initialized:', user.id)
      } else {
        console.error('No user data from Telegram')
        setError('Could not get user data from Telegram')
      }
      
      setLoading(false)
    } else {
      console.error('Telegram WebApp not available')
      setError('This app must be opened in Telegram')
      setLoading(false)
    }
  }, [])

  if (loading) {
    return (
      <div className="app">
        <div className="loading">
          <div className="spinner"></div>
          <p>Loading...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="app">
        <div className="error">
          <h2>Error</h2>
          <p>{error}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="app">
      <Dashboard userId={userId} initData={initData} tg={tg} />
    </div>
  )
}

export default App

