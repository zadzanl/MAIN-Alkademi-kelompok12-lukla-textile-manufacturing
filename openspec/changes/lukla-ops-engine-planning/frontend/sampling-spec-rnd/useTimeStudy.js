/**
 * @name: useTimeStudy
 * @description: Custom React hook untuk manage time study data & API calls
 * @returns: {object} Hook state & methods
 * @example:
 *   const { timeStudies, loading, createTimeStudy } = useTimeStudy()
 */

import { useState, useCallback, useEffect } from 'react'
import { apiClient } from '../utils/api-client'


/**
 * Custom hook untuk Time Study management
 * 
 * State:
 * - timeStudies: Array of time studies
 * - currentTimeStudy: Currently selected time study
 * - loading: Loading state
 * - error: Error message
 * - analysis: Analysis result untuk current study
 * 
 * Methods:
 * - createTimeStudy: Create time study
 * - getTimeStudy: Get specific time study
 * - listTimeStudies: Get all time studies (filtered)
 * - analyzeTimeStudy: Analyze time study
 * - deleteTimeStudy: Delete time study
 */
export const useTimeStudy = () => {
  // State
  const [timeStudies, setTimeStudies] = useState([])
  const [currentTimeStudy, setCurrentTimeStudy] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [analysis, setAnalysis] = useState(null)

  // ============================================
  // CREATE TIME STUDY
  // ============================================
  const createTimeStudy = useCallback(async (data) => {
    /**
     * Create time study baru
     * 
     * @param {object} data - Time study data
     *   {
     *     spec_id: "spec-123",
     *     product_id: "prod-001",
     *     operator: "operator-001",
     *     phases: [
     *       { name: "Potong", duration: 120, notes: "Normal" },
     *       { name: "Jahit", duration: 180, notes: "Smooth" }
     *     ]
     *   }
     * @returns {object} Created time study
     */
    try {
      setLoading(true)
      setError(null)

      const response = await apiClient.post('/time-studies', data)
      
      if (response.success) {
        setTimeStudies([...timeStudies, response.data])
        setCurrentTimeStudy(response.data)
        return response.data
      } else {
        throw new Error(response.error || 'Failed to create time study')
      }
    } catch (err) {
      setError(err.message)
      throw err
    } finally {
      setLoading(false)
    }
  }, [timeStudies])

  // ============================================
  // GET TIME STUDY
  // ============================================
  const getTimeStudy = useCallback(async (timeStudyId) => {
    /**
     * Get specific time study by ID
     * 
     * @param {string} timeStudyId - Time study ID
     * @returns {object} Time study data
     */
    try {
      setLoading(true)
      setError(null)

      const response = await apiClient.get(`/time-studies/${timeStudyId}`)
      
      if (response.success) {
        setCurrentTimeStudy(response.data)
        return response.data
      } else {
        throw new Error(response.error || 'Failed to get time study')
      }
    } catch (err) {
      setError(err.message)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  // ============================================
  // LIST TIME STUDIES
  // ============================================
  const listTimeStudies = useCallback(async (filters = {}) => {
    /**
     * List time studies dengan optional filters
     * 
     * @param {object} filters - Filter options
     *   {
     *     spec_id: "spec-123",
     *     product_id: "prod-001",
     *     status: "completed",
     *     limit: 50,
     *     offset: 0
     *   }
     * @returns {array} List of time studies
     */
    try {
      setLoading(true)
      setError(null)

      const queryParams = new URLSearchParams(filters).toString()
      const response = await apiClient.get(`/time-studies?${queryParams}`)
      
      if (response.success) {
        setTimeStudies(response.data)
        return response.data
      } else {
        throw new Error(response.error || 'Failed to list time studies')
      }
    } catch (err) {
      setError(err.message)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  // ============================================
  // ANALYZE TIME STUDY
  // ============================================
  const analyzeTimeStudy = useCallback(async (timeStudyId) => {
    /**
     * Analyze time study dan hitung statistics
     * 
     * @param {string} timeStudyId - Time study ID
     * @returns {object} Analysis result
     */
    try {
      setLoading(true)
      setError(null)

      const response = await apiClient.post(`/time-studies/${timeStudyId}/analyze`, {})
      
      if (response.success) {
        setAnalysis(response.data)
        return response.data
      } else {
        throw new Error(response.error || 'Failed to analyze time study')
      }
    } catch (err) {
      setError(err.message)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  // ============================================
  // DELETE TIME STUDY
  // ============================================
  const deleteTimeStudy = useCallback(async (timeStudyId) => {
    /**
     * Delete time study
     * 
     * @param {string} timeStudyId - Time study ID
     * @returns {boolean} Success
     */
    try {
      setLoading(true)
      setError(null)

      const response = await apiClient.delete(`/time-studies/${timeStudyId}`)
      
      if (response.success) {
        setTimeStudies(timeStudies.filter(ts => ts.id !== timeStudyId))
        if (currentTimeStudy?.id === timeStudyId) {
          setCurrentTimeStudy(null)
        }
        return true
      } else {
        throw new Error(response.error || 'Failed to delete time study')
      }
    } catch (err) {
      setError(err.message)
      throw err
    } finally {
      setLoading(false)
    }
  }, [timeStudies, currentTimeStudy])

  // ============================================
  // RESET ERROR
  // ============================================
  const clearError = useCallback(() => {
    setError(null)
  }, [])

  // ============================================
  // RETURN HOOK STATE & METHODS
  // ============================================
  return {
    // State
    timeStudies,
    currentTimeStudy,
    loading,
    error,
    analysis,

    // Methods
    createTimeStudy,
    getTimeStudy,
    listTimeStudies,
    analyzeTimeStudy,
    deleteTimeStudy,
    clearError,

    // Setters (if needed)
    setCurrentTimeStudy,
    setTimeStudies,
  }
}

export default useTimeStudy
