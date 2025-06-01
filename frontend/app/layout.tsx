// ABOUTME: Root layout component for Next.js App Router
// ABOUTME: Defines global layout, metadata, and providers

import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'AWS Computer Use Demo',
  description: 'AI-powered desktop automation using Amazon Bedrock and Claude',
  keywords: ['AI', 'automation', 'AWS', 'Bedrock', 'Claude', 'computer use'],
  authors: [{ name: 'Maddy Ravipati' }],
  openGraph: {
    title: 'AWS Computer Use Demo',
    description: 'AI-powered desktop automation using Amazon Bedrock and Claude',
    type: 'website',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <div className="relative min-h-screen bg-background">
          {children}
        </div>
      </body>
    </html>
  )
}