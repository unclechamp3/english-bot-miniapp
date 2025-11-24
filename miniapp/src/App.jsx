import { useEffect, useState } from 'react'
import Dashboard from './components/Dashboard'
import Vocabulary from './components/Vocabulary'
import './App.css'

function App() {
  const [tg, setTg] = useState(null)
  const [userId, setUserId] = useState(null)
  const [initData, setInitData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('analytics') // 'analytics' or 'vocabulary'

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
      
      console.log('Telegram WebApp data:', {
        hasInitData: !!data,
        initDataLength: data?.length,
        hasUser: !!user,
        userId: user?.id
      })
      
      if (user && user.id) {
        setUserId(user.id)
        // initData может быть пустым в некоторых случаях, но user есть
        if (data) {
          setInitData(data)
        } else {
          console.warn('initData is empty, but user data is available')
          // Попробуем использовать initDataUnsafe для создания строки
          setInitData('')
        }
        console.log('Telegram user initialized:', user.id)
      } else {
        console.error('No user data from Telegram', { user, data })
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
      {/* Navigation Tabs */}
      <div className="app-tabs">
        <button 
          className={`app-tab ${activeTab === 'analytics' ? 'active' : ''}`}
          onClick={() => setActiveTab('analytics')}
        >
          📊 Analytics
        </button>
        <button 
          className={`app-tab ${activeTab === 'vocabulary' ? 'active' : ''}`}
          onClick={() => setActiveTab('vocabulary')}
        >
          📚 Vocabulary
        </button>
      </div>

      {/* Content */}
      {activeTab === 'analytics' ? (
        <Dashboard userId={userId} initData={initData} tg={tg} />
      ) : (
        <Vocabulary userId={userId} initData={initData} tg={tg} />
      )}
    </div>
  )
}

export default App

