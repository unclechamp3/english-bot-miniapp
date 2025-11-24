import { useState, useEffect } from 'react'
import { getUserVocabulary, getDueWords, reviewWord, addWord, deleteWord } from '../services/vocabularyApi'
import './Vocabulary.css'

function Vocabulary({ userId, initData, tg }) {
  const [words, setWords] = useState([])
  const [stats, setStats] = useState(null)
  const [dueWords, setDueWords] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('words') // 'words' or 'review'
  const [reviewIndex, setReviewIndex] = useState(0)
  const [newWord, setNewWord] = useState('')
  const [addingWord, setAddingWord] = useState(false)

  useEffect(() => {
    fetchVocabulary()
  }, [userId, initData])

  async function fetchVocabulary() {
    try {
      setLoading(true)
      setError(null)

      const [vocabData, dueData] = await Promise.all([
        getUserVocabulary(userId, initData),
        getDueWords(userId, initData, 5)
      ])

      setWords(vocabData.words || [])
      setStats(vocabData.stats || {})
      setDueWords(dueData.due_words || [])
    } catch (err) {
      console.error('Error fetching vocabulary:', err)
      setError(err.message)
      
      if (tg) {
        tg.showAlert('Failed to load vocabulary: ' + err.message)
      }
    } finally {
      setLoading(false)
    }
  }

  async function handleReview(correct) {
    if (reviewIndex >= dueWords.length) return

    const word = dueWords[reviewIndex]
    
    try {
      await reviewWord(userId, initData, word.word, correct)
      
      // Move to next word
      if (reviewIndex + 1 >= dueWords.length) {
        // Review complete
        setActiveTab('words')
        setReviewIndex(0)
        fetchVocabulary() // Refresh data
        if (tg) {
          tg.showAlert('Review session completed! 🎉')
        }
      } else {
        setReviewIndex(reviewIndex + 1)
      }
    } catch (err) {
      console.error('Error reviewing word:', err)
      if (tg) {
        tg.showAlert('Error reviewing word: ' + err.message)
      }
    }
  }

  async function handleAddWord() {
    if (!newWord.trim()) return

    try {
      setAddingWord(true)
      await addWord(userId, initData, newWord.trim())
      setNewWord('')
      fetchVocabulary()
      if (tg) {
        tg.showAlert(`Added "${newWord}" to your vocabulary!`)
      }
    } catch (err) {
      console.error('Error adding word:', err)
      if (tg) {
        tg.showAlert('Error adding word: ' + err.message)
      }
    } finally {
      setAddingWord(false)
    }
  }

  if (loading) {
    return (
      <div className="vocabulary">
        <div className="loading">
          <div className="spinner"></div>
          <p>Loading vocabulary...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="vocabulary">
        <div className="error">
          <h2>Error Loading Vocabulary</h2>
          <p>{error}</p>
          <button 
            className="retry-button"
            onClick={() => fetchVocabulary()}
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="vocabulary">
      <div className="vocabulary-header">
        <h1>📚 Vocabulary</h1>
        <p className="vocabulary-subtitle">Learn and practice new words</p>
      </div>

      {/* Tabs */}
      <div className="tabs">
        <button 
          className={`tab ${activeTab === 'words' ? 'active' : ''}`}
          onClick={() => setActiveTab('words')}
        >
          📖 My Words
        </button>
        <button 
          className={`tab ${activeTab === 'review' ? 'active' : ''}`}
          onClick={() => {
            setActiveTab('review')
            setReviewIndex(0)
          }}
          disabled={dueWords.length === 0}
        >
          🔄 Review {dueWords.length > 0 && `(${dueWords.length})`}
        </button>
      </div>

      {/* Stats */}
      {stats && (
        <div className="vocab-stats">
          <div className="stat-item">
            <span className="stat-value">{stats.total}</span>
            <span className="stat-label">Total</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">{stats.new}</span>
            <span className="stat-label">New</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">{stats.learning}</span>
            <span className="stat-label">Learning</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">{stats.mastered}</span>
            <span className="stat-label">Mastered</span>
          </div>
        </div>
      )}

      {/* Words List Tab */}
      {activeTab === 'words' && (
        <div className="words-tab">
          {/* Add Word Form */}
          <div className="add-word-form">
            <input
              type="text"
              value={newWord}
              onChange={(e) => setNewWord(e.target.value)}
              placeholder="Enter a word to add..."
              disabled={addingWord}
              onKeyPress={(e) => e.key === 'Enter' && handleAddWord()}
            />
            <button 
              onClick={handleAddWord}
              disabled={addingWord || !newWord.trim()}
            >
              {addingWord ? '...' : '+ Add'}
            </button>
          </div>

          {/* Words List */}
          {words.length === 0 ? (
            <div className="no-words">
              <p>📚 No words yet!</p>
              <p>Add your first word above</p>
            </div>
          ) : (
            <div className="words-list">
              {words.map((word, index) => (
                <div key={index} className={`word-card ${word.status}`}>
                  <div className="word-header">
                    <h3>{word.word}</h3>
                    <span className={`status-badge ${word.status}`}>
                      {word.status}
                    </span>
                  </div>
                  <p className="translation">🇷🇺 {word.translation}</p>
                  <p className="example">💬 {word.example}</p>
                  <div className="word-footer">
                    <span className="next-review">
                      Next: {new Date(word.next_review).toLocaleDateString()}
                    </span>
                    <span className="reviews">
                      ✅ {word.correct_count}/{word.reviews_count}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Review Tab */}
      {activeTab === 'review' && (
        <div className="review-tab">
          {dueWords.length === 0 ? (
            <div className="no-review">
              <h2>✅ All caught up!</h2>
              <p>No words to review right now.</p>
              <p>Come back tomorrow!</p>
            </div>
          ) : reviewIndex < dueWords.length ? (
            <div className="review-card">
              <div className="review-progress">
                {reviewIndex + 1} / {dueWords.length}
              </div>
              <div className="review-word">
                <h2>{dueWords[reviewIndex].word}</h2>
                <p className="translation">
                  🇷🇺 {dueWords[reviewIndex].translation}
                </p>
                <p className="example">
                  💬 {dueWords[reviewIndex].example}
                </p>
              </div>
              <div className="review-buttons">
                <button 
                  className="forgot-button"
                  onClick={() => handleReview(false)}
                >
                  ❌ I Forgot
                </button>
                <button 
                  className="know-button"
                  onClick={() => handleReview(true)}
                >
                  ✅ I Know
                </button>
              </div>
            </div>
          ) : (
            <div className="review-complete">
              <h2>🎉 Review Complete!</h2>
              <p>Great job!</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default Vocabulary

