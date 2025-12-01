"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts"
import { getDashboardSummary, getTimeSeries, getLogs } from "@/lib/api"
import type { DashboardSummary, TimeSeriesResponse, LogListResponse } from "@/lib/types"
import { useTranslations } from "@/lib/use-translations"

export default function OverviewContent() {
  const t = useTranslations()
  const [summary, setSummary] = useState<DashboardSummary | null>(null)
  const [timeSeries, setTimeSeries] = useState<TimeSeriesResponse | null>(null)
  const [recentLogs, setRecentLogs] = useState<LogListResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true)
        const [summaryData, timeSeriesData, logsData] = await Promise.all([
          getDashboardSummary(),
          getTimeSeries(30),
          getLogs(1, 5),
        ])
        setSummary(summaryData)
        setTimeSeries(timeSeriesData)
        setRecentLogs(logsData)
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to fetch data")
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  const formatLatency = (ms: number | null) => {
    if (ms === null) return "N/A"
    if (ms < 1000) return `${Math.round(ms)}ms`
    return `${(ms / 1000).toFixed(2)}s`
  }

  const formatScore = (score: number | null) => {
    if (score === null) return "N/A"
    return score.toFixed(2)
  }

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">{t.overview.title}</h1>
        <p className="text-muted-foreground">
          {t.overview.subtitle}
        </p>
      </div>

      {error && (
        <Card className="border-red-500">
          <CardContent className="pt-6">
            <p className="text-sm text-red-500">{t.common.error} {error}</p>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{t.overview.totalLogs}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {loading ? t.common.loading : summary?.total_logs || 0}
            </div>
            <p className="text-xs text-muted-foreground">
              {t.overview.totalLogsDesc}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{t.overview.evaluated}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {loading ? t.common.loading : summary?.total_evaluated || 0}
            </div>
            <p className="text-xs text-muted-foreground">
              {t.overview.evaluatedDesc}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{t.overview.avgLatency}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {loading ? t.common.loading : formatLatency(summary?.avg_latency_ms || null)}
            </div>
            <p className="text-xs text-muted-foreground">
              {t.overview.avgLatencyDesc}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{t.overview.avgScore}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {loading ? t.common.loading : formatScore(summary?.avg_score || null)}
            </div>
            <p className="text-xs text-muted-foreground">
              {t.overview.avgScoreDesc}
            </p>
          </CardContent>
        </Card>
      </div>

      {timeSeries && timeSeries.data.length > 0 && (
        <div className="grid gap-4 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>{t.overview.qualityTrend}</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={timeSeries.data}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis domain={[0, 5]} />
                  <Tooltip />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="avg_score"
                    stroke="#10b981"
                    strokeWidth={2}
                    name="Avg Score"
                    dot={{ r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>{t.overview.latencyTrend}</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={timeSeries.data}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip
                    formatter={(value: number) => formatLatency(value)}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="avg_latency_ms"
                    stroke="#3b82f6"
                    strokeWidth={2}
                    name="Avg Latency (ms)"
                    dot={{ r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>
      )}

      {timeSeries && timeSeries.data.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>{t.overview.volumeTrend}</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={timeSeries.data}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" />
                <Tooltip />
                <Legend />
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="total_requests"
                  stroke="#8b5cf6"
                  strokeWidth={2}
                  name="Total Requests"
                  dot={{ r: 4 }}
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="total_evaluated"
                  stroke="#f59e0b"
                  strokeWidth={2}
                  name="Evaluated"
                  dot={{ r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      {recentLogs && recentLogs.logs.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>{t.overview.recentActivity}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {recentLogs.logs.map((log) => (
                <div key={log.id} className="flex items-center justify-between border-b pb-2 last:border-0">
                  <div className="flex-1">
                    <p className="text-sm font-medium">
                      {log.prompt.length > 60 ? log.prompt.substring(0, 60) + "..." : log.prompt}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {new Date(log.created_at).toLocaleString()} • {log.model_version}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium">{formatLatency(log.latency_ms)}</p>
                    <p className="text-xs text-muted-foreground">{log.status}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>{t.overview.welcome}</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            {t.overview.welcomeDesc}
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
