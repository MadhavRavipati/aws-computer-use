// ABOUTME: Custom hook for WebSocket connections
// ABOUTME: Manages WebSocket lifecycle and message handling

import { useEffect, useRef, useState, useCallback } from 'react'

interface UseWebSocketReturn {
  sendMessage: (message: string) => void
  lastMessage: MessageEvent | null
  readyState: number
}

export function useWebSocket(url: string): UseWebSocketReturn {
  const [lastMessage, setLastMessage] = useState<MessageEvent | null>(null)
  const [readyState, setReadyState] = useState<number>(WebSocket.CONNECTING)
  const ws = useRef<WebSocket | null>(null)
  const reconnectTimeout = useRef<NodeJS.Timeout>()
  const reconnectAttempts = useRef(0)

  const connect = useCallback(() => {
    try {
      ws.current = new WebSocket(url)

      ws.current.onopen = () => {
        console.log('WebSocket connected')
        setReadyState(WebSocket.OPEN)
        reconnectAttempts.current = 0
      }

      ws.current.onmessage = (event) => {
        setLastMessage(event)
      }

      ws.current.onclose = () => {
        console.log('WebSocket disconnected')
        setReadyState(WebSocket.CLOSED)
        
        // Attempt to reconnect with exponential backoff
        if (reconnectAttempts.current < 5) {
          const timeout = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000)
          reconnectTimeout.current = setTimeout(() => {
            reconnectAttempts.current++
            connect()
          }, timeout)
        }
      }

      ws.current.onerror = (error) => {
        console.error('WebSocket error:', error)
        setReadyState(WebSocket.CLOSED)
      }
    } catch (error) {
      console.error('Failed to connect WebSocket:', error)
    }
  }, [url])

  useEffect(() => {
    connect()

    return () => {
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current)
      }
      if (ws.current) {
        ws.current.close()
      }
    }
  }, [connect])

  const sendMessage = useCallback((message: string) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(message)
    } else {
      console.warn('WebSocket is not connected')
    }
  }, [])

  return {
    sendMessage,
    lastMessage,
    readyState,
  }
}