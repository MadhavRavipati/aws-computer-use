// ABOUTME: Custom hook for API interactions
// ABOUTME: Provides typed HTTP methods with error handling

import { useCallback } from 'react'

const API_ENDPOINT = process.env.NEXT_PUBLIC_API_ENDPOINT || 'http://localhost:8000'

interface ApiError extends Error {
  status?: number
  data?: any
}

export function useApi() {
  const request = useCallback(async <T = any>(
    path: string,
    options: RequestInit = {}
  ): Promise<T> => {
    const url = `${API_ENDPOINT}${path}`
    
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    })

    const data = await response.json()

    if (!response.ok) {
      const error = new Error(data.error || 'API request failed') as ApiError
      error.status = response.status
      error.data = data
      throw error
    }

    return data
  }, [])

  const get = useCallback(<T = any>(path: string) => {
    return request<T>(path, { method: 'GET' })
  }, [request])

  const post = useCallback(<T = any>(path: string, body: any) => {
    return request<T>(path, {
      method: 'POST',
      body: JSON.stringify(body),
    })
  }, [request])

  const put = useCallback(<T = any>(path: string, body: any) => {
    return request<T>(path, {
      method: 'PUT',
      body: JSON.stringify(body),
    })
  }, [request])

  const del = useCallback(<T = any>(path: string) => {
    return request<T>(path, { method: 'DELETE' })
  }, [request])

  return { get, post, put, del, request }
}