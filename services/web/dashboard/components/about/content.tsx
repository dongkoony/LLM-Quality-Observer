"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Activity, Database, Zap, BarChart2 } from "lucide-react"

export default function AboutContent() {
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">About</h1>
        <p className="text-muted-foreground">
          LLM Quality Observer - MLOps platform for monitoring LLM response quality
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Project Overview</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm">
            LLM Quality Observer is a microservices-based MLOps platform designed to monitor,
            evaluate, and visualize the quality of Large Language Model (LLM) responses in real-time.
          </p>
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5 text-blue-600" />
              Gateway API
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Handles LLM requests, logs interactions, and tracks latency metrics
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Zap className="h-5 w-5 text-yellow-600" />
              Evaluator Service
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Evaluates response quality using rule-based approaches
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Database className="h-5 w-5 text-green-600" />
              Dashboard API
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Aggregates metrics and provides REST endpoints
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart2 className="h-5 w-5 text-purple-600" />
              Web Dashboard
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Modern Next.js UI for monitoring quality metrics
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Tech Stack</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
            <div>
              <p className="font-medium">Backend</p>
              <ul className="mt-2 space-y-1 text-muted-foreground">
                <li>• Python 3.12</li>
                <li>• FastAPI</li>
                <li>• PostgreSQL 16</li>
              </ul>
            </div>
            <div>
              <p className="font-medium">Frontend</p>
              <ul className="mt-2 space-y-1 text-muted-foreground">
                <li>• Next.js 14</li>
                <li>• TypeScript</li>
                <li>• Tailwind CSS</li>
              </ul>
            </div>
            <div>
              <p className="font-medium">DevOps</p>
              <ul className="mt-2 space-y-1 text-muted-foreground">
                <li>• Docker</li>
                <li>• Docker Compose</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
