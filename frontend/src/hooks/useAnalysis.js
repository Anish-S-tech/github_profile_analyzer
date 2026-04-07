import { useState, useCallback } from 'react'
import { analyzeUser } from '../api/api'

export function useAnalysis() {
  const [data,    setData]    = useState(null)
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState(null)

  const analyze = useCallback(async (username, useLlm = true) => {
    setLoading(true)
    setError(null)
    setData(null)
    try {
      const result = await analyzeUser(username, useLlm)
      if (result.error) throw new Error(result.error)
      setData(result)
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }, [])

  const reset = useCallback(() => {
    setData(null)
    setError(null)
  }, [])

  return { data, loading, error, analyze, reset }
}
