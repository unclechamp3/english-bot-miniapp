/**
 * Vocabulary API client for communicating with FastAPI backend
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

/**
 * Make authenticated request to API
 */
async function apiRequest(endpoint, initData, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`
  
  console.log('Vocabulary API Request:', {
    url,
    hasInitData: !!initData,
    endpoint
  })
  
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  }
  
  if (initData && initData.trim()) {
    headers['X-Telegram-Init-Data'] = initData
  }
  
  const response = await fetch(url, {
    ...options,
    headers,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
    console.error('Vocabulary API Error:', error)
    throw new Error(error.detail || `HTTP ${response.status}`)
  }

  return response.json()
}

/**
 * Get user's vocabulary
 */
export async function getUserVocabulary(userId, initData, status = null) {
  const statusParam = status ? `?status=${status}` : ''
  return apiRequest(`/api/vocabulary/${userId}${statusParam}`, initData)
}

/**
 * Get words due for review
 */
export async function getDueWords(userId, initData, limit = 5) {
  return apiRequest(`/api/vocabulary/${userId}/due?limit=${limit}`, initData)
}

/**
 * Add a new word
 */
export async function addWord(userId, initData, word) {
  return apiRequest(`/api/vocabulary/${userId}/add`, initData, {
    method: 'POST',
    body: JSON.stringify({ word })
  })
}

/**
 * Review a word (mark as correct or forgot)
 */
export async function reviewWord(userId, initData, word, correct) {
  return apiRequest(`/api/vocabulary/${userId}/review`, initData, {
    method: 'POST',
    body: JSON.stringify({ word, correct })
  })
}

/**
 * Delete a word
 */
export async function deleteWord(userId, initData, word) {
  return apiRequest(`/api/vocabulary/${userId}/${word}`, initData, {
    method: 'DELETE'
  })
}

/**
 * Get vocabulary statistics
 */
export async function getVocabularyStats(userId, initData) {
  return apiRequest(`/api/vocabulary/${userId}/stats`, initData)
}

