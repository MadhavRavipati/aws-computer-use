// ABOUTME: Custom hook for session management
// ABOUTME: Handles session creation, termination, and status updates

import { useState, useCallback } from 'react'
import { useApi } from './use-api'

export interface Session {
  session_id: string
  user_id: string
  status: string
  task_id?: string
  websocket_url?: string
  vnc_url?: string
  created_at?: number
  private_ip?: string
}

export function useSession() {
  const [session, setSession] = useState<Session | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { post, get, del } = useApi()

  const createSession = useCallback(async (userId: string) => {
    setIsLoading(true)
    setError(null)
    
    try {
      const response = await post<Session>('/sessions', { user_id: userId })
      setSession(response)
      return response
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to create session'
      setError(message)
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [post])

  const getSessionStatus = useCallback(async (sessionId: string) => {
    try {
      const response = await get<Session>(`/sessions/${sessionId}`)
      setSession(response)
      return response
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to get session status'
      setError(message)
      throw err
    }
  }, [get])

  const terminateSession = useCallback(async (sessionId: string) => {
    setIsLoading(true)
    setError(null)
    
    try {
      await del(`/sessions/${sessionId}`)
      setSession(null)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to terminate session'
      setError(message)
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [del])

  return {
    session,
    isLoading,
    error,
    createSession,
    getSessionStatus,
    terminateSession,
  }
}