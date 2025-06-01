// ABOUTME: Home page component for Computer Use Demo
// ABOUTME: Main entry point with session management and VNC viewer

'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { SessionList } from '@/components/session-list'
import { VNCViewer } from '@/components/vnc-viewer'
import { ChatInterface } from '@/components/chat-interface'
import { useSession } from '@/hooks/use-session'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Loader2, Monitor, MessageSquare, Settings } from 'lucide-react'

export default function HomePage() {
  const { session, isLoading, createSession, terminateSession } = useSession()
  const [userId, setUserId] = useState('')

  const handleCreateSession = async () => {
    await createSession(userId || 'anonymous')
  }

  const handleTerminateSession = async () => {
    if (session) {
      await terminateSession(session.session_id)
    }
  }

  return (
    <div className="container mx-auto p-4 max-w-7xl">
      <header className="mb-8">
        <h1 className="text-4xl font-bold mb-2">AWS Computer Use Demo</h1>
        <p className="text-muted-foreground">
          AI-powered desktop automation using Amazon Bedrock and Claude
        </p>
      </header>

      {!session ? (
        <div className="grid gap-6 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Create New Session</CardTitle>
              <CardDescription>
                Start a new desktop session with AI control
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="userId">User ID (optional)</Label>
                  <Input
                    id="userId"
                    placeholder="Enter your user ID or leave blank"
                    value={userId}
                    onChange={(e) => setUserId(e.target.value)}
                  />
                </div>
                <Button
                  onClick={handleCreateSession}
                  disabled={isLoading}
                  className="w-full"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Creating Session...
                    </>
                  ) : (
                    <>
                      <Monitor className="mr-2 h-4 w-4" />
                      Create Session
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Your Sessions</CardTitle>
              <CardDescription>
                View and manage your active sessions
              </CardDescription>
            </CardHeader>
            <CardContent>
              <SessionList userId={userId || 'anonymous'} />
            </CardContent>
          </Card>
        </div>
      ) : (
        <div className="space-y-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Active Session</CardTitle>
                <CardDescription>
                  Session ID: {session.session_id}
                </CardDescription>
              </div>
              <Button
                variant="destructive"
                onClick={handleTerminateSession}
                disabled={isLoading}
              >
                Terminate Session
              </Button>
            </CardHeader>
          </Card>

          <Tabs defaultValue="desktop" className="w-full">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="desktop">
                <Monitor className="mr-2 h-4 w-4" />
                Desktop
              </TabsTrigger>
              <TabsTrigger value="chat">
                <MessageSquare className="mr-2 h-4 w-4" />
                AI Assistant
              </TabsTrigger>
              <TabsTrigger value="settings">
                <Settings className="mr-2 h-4 w-4" />
                Settings
              </TabsTrigger>
            </TabsList>

            <TabsContent value="desktop" className="mt-6">
              <Card>
                <CardContent className="p-0">
                  <div className="aspect-video">
                    <VNCViewer sessionId={session.session_id} />
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="chat" className="mt-6">
              <ChatInterface sessionId={session.session_id} />
            </TabsContent>

            <TabsContent value="settings" className="mt-6">
              <Card>
                <CardHeader>
                  <CardTitle>Session Settings</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <Label>VNC URL</Label>
                      <Input
                        value={session.vnc_url || 'Connecting...'}
                        readOnly
                      />
                    </div>
                    <div>
                      <Label>WebSocket URL</Label>
                      <Input
                        value={session.websocket_url || 'Connecting...'}
                        readOnly
                      />
                    </div>
                    <div>
                      <Label>Status</Label>
                      <Input
                        value={session.status || 'Unknown'}
                        readOnly
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      )}
    </div>
  )
}