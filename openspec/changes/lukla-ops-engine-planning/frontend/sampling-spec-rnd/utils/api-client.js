/**
 * @name: API Client
 * @description: Centralized API communication utility untuk frontend
 * @usage:
 *   import { apiClient } from './api-client'
 *   apiClient.get('/time-studies')
 *   apiClient.post('/time-studies', data)
 */

/**
 * Configuration
 */
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api/v1'
const DEFAULT_TIMEOUT = 30000 // 30 seconds

/**
 * API Client Class
 */
class APIClient {
  constructor(baseURL = API_BASE_URL) {
    this.baseURL = baseURL
    this.timeout = DEFAULT_TIMEOUT
    this.headers = {
      'Content-Type': 'application/json',
    }
    this.token = null
  }

  /**
   * Set authorization token
   * @param {string} token - JWT token
   */
  setToken(token) {
    this.token = token
    if (token) {
      this.headers['Authorization'] = `Bearer ${token}`
    } else {
      delete this.headers['Authorization']
    }
  }

  /**
   * Make HTTP request
   * @private
   */
  async request(method, endpoint, data = null, customHeaders = {}) {
    const url = `${this.baseURL}${endpoint}`
    const options = {
      method,
      headers: { ...this.headers, ...customHeaders },
      timeout: this.timeout,
    }

    // Add body untuk POST, PUT, PATCH
    if (data && ['POST', 'PUT', 'PATCH'].includes(method)) {
      options.body = JSON.stringify(data)
    }

    try {
      const response = await fetch(url, options)
      
      // Handle non-JSON responses
      const contentType = response.headers.get('content-type')
      let result

      if (contentType && contentType.includes('application/json')) {
        result = await response.json()
      } else {
        const text = await response.text()
        result = {
          success: response.ok,
          data: text,
        }
      }

      // Handle errors
      if (!response.ok) {
        throw new Error(
          result.error || `HTTP ${response.status}: ${response.statusText}`
        )
      }

      return result
    } catch (error) {
      console.error(`API Error [${method} ${endpoint}]:`, error)
      throw error
    }
  }

  /**
   * GET request
   * @param {string} endpoint - API endpoint
   * @param {object} params - Query parameters
   * @returns {object} Response
   */
  async get(endpoint, params = {}) {
    const queryString = new URLSearchParams(params).toString()
    const url = queryString ? `${endpoint}?${queryString}` : endpoint
    return this.request('GET', url)
  }

  /**
   * POST request
   * @param {string} endpoint - API endpoint
   * @param {object} data - Request body
   * @returns {object} Response
   */
  async post(endpoint, data) {
    return this.request('POST', endpoint, data)
  }

  /**
   * PUT request
   * @param {string} endpoint - API endpoint
   * @param {object} data - Request body
   * @returns {object} Response
   */
  async put(endpoint, data) {
    return this.request('PUT', endpoint, data)
  }

  /**
   * PATCH request
   * @param {string} endpoint - API endpoint
   * @param {object} data - Request body
   * @returns {object} Response
   */
  async patch(endpoint, data) {
    return this.request('PATCH', endpoint, data)
  }

  /**
   * DELETE request
   * @param {string} endpoint - API endpoint
   * @returns {object} Response
   */
  async delete(endpoint) {
    return this.request('DELETE', endpoint)
  }

  /**
   * File upload (multipart/form-data)
   * @param {string} endpoint - API endpoint
   * @param {FormData} formData - Form data dengan files
   * @returns {object} Response
   */
  async uploadFile(endpoint, formData) {
    const url = `${this.baseURL}${endpoint}`
    const headers = { ...this.headers }
    delete headers['Content-Type'] // Let browser set content-type untuk multipart

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers,
        body: formData,
        timeout: this.timeout,
      })

      const result = await response.json()

      if (!response.ok) {
        throw new Error(result.error || `HTTP ${response.status}`)
      }

      return result
    } catch (error) {
      console.error(`Upload Error [${endpoint}]:`, error)
      throw error
    }
  }

  /**
   * Batch requests
   * @param {array} requests - Array of requests
   *   [
   *     { method: 'GET', endpoint: '/time-studies' },
   *     { method: 'POST', endpoint: '/time-studies', data: {...} }
   *   ]
   * @returns {array} Array of responses
   */
  async batch(requests) {
    try {
      const promises = requests.map(req => {
        switch (req.method) {
          case 'GET':
            return this.get(req.endpoint, req.params)
          case 'POST':
            return this.post(req.endpoint, req.data)
          case 'PUT':
            return this.put(req.endpoint, req.data)
          case 'PATCH':
            return this.patch(req.endpoint, req.data)
          case 'DELETE':
            return this.delete(req.endpoint)
          default:
            throw new Error(`Unknown method: ${req.method}`)
        }
      })

      return await Promise.all(promises)
    } catch (error) {
      console.error('Batch request error:', error)
      throw error
    }
  }

  /**
   * Set custom headers
   * @param {object} headers - Headers to merge
   */
  setHeaders(headers) {
    this.headers = { ...this.headers, ...headers }
  }

  /**
   * Set timeout
   * @param {number} ms - Timeout in milliseconds
   */
  setTimeout(ms) {
    this.timeout = ms
  }
}

/**
 * Create singleton instance
 */
export const apiClient = new APIClient()

/**
 * Default export
 */
export default apiClient
