/**
 * API client for communicating with FastAPI backend
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

/**
 * Make authenticated request to API
 * @param {string} endpoint - API endpoint (e.g., '/api/analytics/123')
 * @param {string} initData - Telegram initData for authentication
 * @param {object} options - Fetch options
 * @returns {Promise<any>} Response data
 */
async function apiRequest(endpoint, initData, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`
  
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'X-Telegram-Init-Data': initData,
      ...options.headers,
    },
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }

  return response.json()
}

/**
 * Get user analytics data
 * @param {number} userId - Telegram user ID
 * @param {string} initData - Telegram initData
 * @returns {Promise<object>} Analytics data
 */
export async function getUserAnalytics(userId, initData) {
  return apiRequest(`/api/analytics/${userId}`, initData)
}

/**
 * Get chart data for user
 * @param {number} userId - Telegram user ID
 * @param {string} initData - Telegram initData
 * @param {number} days - Number of days (default: 7)
 * @returns {Promise<object>} Chart data
 */
export async function getChartData(userId, initData, days = 7) {
  return apiRequest(`/api/charts/${userId}?days=${days}`, initData)
}

/**
 * Get summary statistics
 * @param {string} initData - Telegram initData
 * @returns {Promise<object>} Summary stats
 */
export async function getSummaryStats(initData) {
  return apiRequest('/api/stats/summary', initData)
}

/**
 * Validate authentication
 * @param {string} initData - Telegram initData
 * @returns {Promise<object>} Validation result
 */
export async function validateAuth(initData) {
  return apiRequest('/api/auth/validate', initData, {
    method: 'POST'
  })
}

