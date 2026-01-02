"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { getModelStats } from "@/lib/api"
import type { ModelStatsResponse } from "@/lib/types"
import { useTranslations } from "@/lib/use-translations"

export default function ModelsContent() {
  const t = useTranslations()
  const [modelStats, setModelStats] = useState<ModelStatsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchModelStats() {
      try {
        setLoading(true)
        const data = await getModelStats()
        setModelStats(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to fetch model stats")
      } finally {
        setLoading(false)
      }
    }

    fetchModelStats()
  }, [])

  const formatLatency = (ms: number | null) => {
    if (ms === null) return t.common.na
    if (ms < 1000) return `${Math.round(ms)}ms`
    return `${(ms / 1000).toFixed(2)}s`
  }

  const formatScore = (score: number | null) => {
    if (score === null) return t.common.na
    return score.toFixed(2)
  }

  const getScoreColor = (score: number | null) => {
    if (score === null) return ""
    if (score >= 4) return "text-green-600"
    if (score >= 3) return "text-yellow-600"
    return "text-red-600"
  }

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">{t.models.title}</h1>
        <p className="text-muted-foreground">
          {t.models.subtitle}
        </p>
      </div>

      {error && (
        <Card className="border-red-500">
          <CardContent className="pt-6">
            <p className="text-sm text-red-500">{t.common.error} {error}</p>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>{t.models.tableTitle}</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8">{t.common.loading}</div>
          ) : modelStats && modelStats.models.length > 0 ? (
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>{t.models.modelVersion}</TableHead>
                    <TableHead className="text-right">{t.models.totalRequests}</TableHead>
                    <TableHead className="text-right">{t.models.evaluatedCount}</TableHead>
                    <TableHead className="text-right">{t.models.avgLatency}</TableHead>
                    <TableHead className="text-right">{t.models.avgScore}</TableHead>
                    <TableHead className="text-right">{t.models.evaluationRate}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {modelStats.models.map((model, index) => {
                    const evaluationRate = model.total_requests > 0
                      ? ((model.total_evaluated / model.total_requests) * 100).toFixed(1)
                      : "0.0"

                    return (
                      <TableRow key={index}>
                        <TableCell className="font-medium">{model.model_version}</TableCell>
                        <TableCell className="text-right">{model.total_requests}</TableCell>
                        <TableCell className="text-right">{model.total_evaluated}</TableCell>
                        <TableCell className="text-right">{formatLatency(model.avg_latency_ms)}</TableCell>
                        <TableCell className={`text-right font-medium ${getScoreColor(model.avg_score)}`}>
                          {formatScore(model.avg_score)}
                        </TableCell>
                        <TableCell className="text-right">{evaluationRate}%</TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              {t.models.noModels}
            </div>
          )}
        </CardContent>
      </Card>

      {modelStats && modelStats.models.length > 0 && (
        <div className="grid gap-4 md:grid-cols-3">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{t.models.totalModels}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{modelStats.models.length}</div>
              <p className="text-xs text-muted-foreground">
                {t.models.totalModelsDesc}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{t.models.bestAvgScore}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {Math.max(...modelStats.models.map(m => m.avg_score || 0)).toFixed(2)}
              </div>
              <p className="text-xs text-muted-foreground">
                {t.models.bestAvgScoreDesc}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{t.models.bestAvgLatency}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {formatLatency(Math.min(...modelStats.models.map(m => m.avg_latency_ms || Infinity)))}
              </div>
              <p className="text-xs text-muted-foreground">
                {t.models.bestAvgLatencyDesc}
              </p>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
