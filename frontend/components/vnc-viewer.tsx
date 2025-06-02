// ABOUTME: VNC viewer component for desktop streaming
// ABOUTME: Integrates noVNC for real-time desktop display

'use client'

import { useEffect, useRef, useState } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Loader2, Maximize2, Minimize2, RefreshCw } from 'lucide-react'
import { useWebSocket } from '@/hooks/use-websocket'

interface VNCViewerProps {
  sessionId: string
}

export function VNCViewer({ sessionId }: VNCViewerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const [screenshot, setScreenshot] = useState<string | null>(null)
  
  const wsUrl = process.env.NEXT_PUBLIC_WS_ENDPOINT 
    ? `${process.env.NEXT_PUBLIC_WS_ENDPOINT}?sessionId=${sessionId}`
    : `ws://localhost:8000/ws/${sessionId}`
    
  const { sendMessage, lastMessage, readyState } = useWebSocket(wsUrl)

  useEffect(() => {
    if (lastMessage) {
      try {
        const data = JSON.parse(lastMessage.data)
        if (data.type === 'screenshot' && data.data) {
          setScreenshot(data.data)
          setIsConnected(true)
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error)
      }
    }
  }, [lastMessage])

  useEffect(() => {
    if (screenshot && canvasRef.current) {
      const img = new Image()
      img.onload = () => {
        const canvas = canvasRef.current
        if (!canvas) return
        
        const ctx = canvas.getContext('2d')
        if (!ctx) return
        
        canvas.width = img.width
        canvas.height = img.height
        ctx.drawImage(img, 0, 0)
      }
      img.src = `data:image/png;base64,${screenshot}`
    }
  }, [screenshot])

  const handleMouseClick = (event: React.MouseEvent<HTMLCanvasElement>) => {
    if (!canvasRef.current) return
    
    const rect = canvasRef.current.getBoundingClientRect()
    const x = Math.round((event.clientX - rect.left) * (canvasRef.current.width / rect.width))
    const y = Math.round((event.clientY - rect.top) * (canvasRef.current.height / rect.height))
    
    sendMessage(JSON.stringify({
      type: 'click',
      x,
      y,
      button: 'left'
    }))
  }

  const handleKeyPress = (event: React.KeyboardEvent) => {
    // Handle special keys
    if (event.ctrlKey || event.metaKey) {
      const keys = []
      if (event.ctrlKey) keys.push('ctrl')
      if (event.metaKey) keys.push('cmd')
      keys.push(event.key.toLowerCase())
      
      sendMessage(JSON.stringify({
        type: 'key_combination',
        keys: keys.join('+')
      }))
    } else {
      // Regular text input
      sendMessage(JSON.stringify({
        type: 'type',
        text: event.key
      }))
    }
  }

  const toggleFullscreen = async () => {
    if (!containerRef.current) return
    
    if (!isFullscreen) {
      await containerRef.current.requestFullscreen()
      setIsFullscreen(true)
    } else {
      await document.exitFullscreen()
      setIsFullscreen(false)
    }
  }

  const refresh = () => {
    sendMessage(JSON.stringify({
      type: 'refresh'
    }))
  }

  return (
    <Card className="w-full h-full">
      <CardContent className="p-0 relative">
        <div className="absolute top-4 right-4 z-10 flex space-x-2">
          <Button
            variant="secondary"
            size="icon"
            onClick={refresh}
            disabled={readyState !== WebSocket.OPEN}
          >
            <RefreshCw className="h-4 w-4" />
          </Button>
          <Button
            variant="secondary"
            size="icon"
            onClick={toggleFullscreen}
          >
            {isFullscreen ? (
              <Minimize2 className="h-4 w-4" />
            ) : (
              <Maximize2 className="h-4 w-4" />
            )}
          </Button>
        </div>
        
        <div
          ref={containerRef}
          className="vnc-container"
          tabIndex={0}
          onKeyDown={handleKeyPress}
        >
          {!isConnected ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
                <p className="text-muted-foreground">Connecting to desktop...</p>
              </div>
            </div>
          ) : (
            <canvas
              ref={canvasRef}
              className="vnc-canvas cursor-pointer"
              onClick={handleMouseClick}
            />
          )}
        </div>
      </CardContent>
    </Card>
  )
}