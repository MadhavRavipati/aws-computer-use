// ABOUTME: Session list component to display user sessions
// ABOUTME: Shows active and past sessions with status indicators

'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useApi } from '@/hooks/use-api'
import { formatDate } from '@/lib/utils'
import { Session } from '@/hooks/use-session'
import { Loader2, Monitor, Trash2 } from 'lucide-react'

interface SessionListProps {
  userId: string
  onSelectSession?: (session: Session) => void
}

export function SessionList({ userId, onSelectSession }: SessionListProps) {
  const [sessions, setSessions] = useState<Session[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const { get, del } = useApi()

  useEffect(() => {
    loadSessions()
  }, [userId])

  const loadSessions = async () => {
    try {
      setIsLoading(true)
      const response = await get<{ sessions: Session[] }>(
        `/sessions?user_id=${userId}`
      )
      setSessions(response.sessions || [])
    } catch (error) {
      console.error('Failed to load sessions:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleDelete = async (sessionId: string) => {
    try {
      await del(`/sessions/${sessionId}`)
      await loadSessions()
    } catch (error) {
      console.error('Failed to delete session:', error)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="h-6 w-6 animate-spin" />
      </div>
    )
  }

  if (sessions.length === 0) {
    return (
      <div className="text-center text-muted-foreground p-8">
        No sessions found
      </div>
    )
  }

  return (
    <div className="space-y-2">
      {sessions.map((session) => (
        <Card key={session.session_id} className="cursor-pointer hover:bg-accent">
          <CardContent className="flex items-center justify-between p-4">
            <div
              className="flex items-center space-x-3 flex-1"
              onClick={() => onSelectSession?.(session)}
            >
              <Monitor className="h-5 w-5 text-muted-foreground" />
              <div>
                <p className="font-medium text-sm">
                  Session {session.session_id.slice(0, 8)}
                </p>
                <p className="text-xs text-muted-foreground">
                  {session.created_at
                    ? formatDate(session.created_at * 1000)
                    : 'Unknown time'}
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <StatusBadge status={session.status} />
              <Button
                variant="ghost"
                size="icon"
                onClick={(e) => {
                  e.stopPropagation()
                  handleDelete(session.session_id)
                }}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}

function StatusBadge({ status }: { status: string }) {
  const statusColors = {
    starting: 'bg-yellow-500',
    running: 'bg-green-500',
    stopping: 'bg-orange-500',
    stopped: 'bg-gray-500',
    terminated: 'bg-red-500',
  }

  const color = statusColors[status as keyof typeof statusColors] || 'bg-gray-500'

  return (
    <div className="flex items-center space-x-2">
      <div className={`h-2 w-2 rounded-full ${color}`} />
      <span className="text-xs capitalize">{status}</span>
    </div>
  )
}