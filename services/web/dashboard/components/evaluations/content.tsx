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
import { Button } from "@/components/ui/button"
import { getEvaluations } from "@/lib/api"
import type { EvaluationListResponse } from "@/lib/types"
import { useTranslations } from "@/lib/use-translations"

export default function EvaluationsContent() {
  const t = useTranslations()
  const [evaluationsData, setEvaluationsData] = useState<EvaluationListResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [currentPage, setCurrentPage] = useState(1)
  const pageSize = 10

  useEffect(() => {
    async function fetchEvaluations() {
      try {
        setLoading(true)
        const data = await getEvaluations(currentPage, pageSize)
        setEvaluationsData(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to fetch evaluations")
      } finally {
        setLoading(false)
      }
    }

    fetchEvaluations()
  }, [currentPage])

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString()
  }

  const truncateText = (text: string, maxLength: number = 80) => {
    if (text.length <= maxLength) return text
    return text.substring(0, maxLength) + "..."
  }

  const getScoreColor = (score: number) => {
    if (score >= 4) return "bg-green-100 text-green-800"
    if (score >= 3) return "bg-yellow-100 text-yellow-800"
    return "bg-red-100 text-red-800"
  }

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">{t.evaluations.title}</h1>
        <p className="text-muted-foreground">
          {t.evaluations.subtitle}
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
          <div className="flex items-center justify-between">
            <CardTitle>{t.evaluations.tableTitle}</CardTitle>
            <div className="text-sm text-muted-foreground">
              {evaluationsData && `${t.evaluations.total} ${evaluationsData.total} ${t.evaluations.evaluationsText} | ${t.logs.page} ${evaluationsData.page} ${t.logs.of} ${evaluationsData.total_pages}`}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8">{t.common.loading}</div>
          ) : evaluationsData && evaluationsData.evaluations.length > 0 ? (
            <div className="space-y-4">
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-[60px]">{t.evaluations.id}</TableHead>
                      <TableHead className="w-[140px]">{t.evaluations.createdAt}</TableHead>
                      <TableHead className="w-[80px]">{t.evaluations.logId}</TableHead>
                      <TableHead>{t.evaluations.prompt}</TableHead>
                      <TableHead>{t.evaluations.response}</TableHead>
                      <TableHead className="w-[80px]">{t.evaluations.score}</TableHead>
                      <TableHead className="w-[80px]">{t.evaluations.label}</TableHead>
                      <TableHead className="w-[100px]">{t.evaluations.judge}</TableHead>
                      <TableHead>{t.evaluations.comment}</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {evaluationsData.evaluations.map((evaluation) => (
                      <TableRow key={evaluation.id}>
                        <TableCell className="font-medium">{evaluation.id}</TableCell>
                        <TableCell className="text-xs">{formatDate(evaluation.created_at)}</TableCell>
                        <TableCell className="text-xs">{evaluation.log_id}</TableCell>
                        <TableCell className="text-xs">{truncateText(evaluation.log_prompt || t.common.na, 60)}</TableCell>
                        <TableCell className="text-xs">{truncateText(evaluation.log_response || t.common.na, 60)}</TableCell>
                        <TableCell>
                          <span className={`text-xs px-2 py-1 rounded ${getScoreColor(evaluation.overall_score)}`}>
                            {evaluation.overall_score}/5
                          </span>
                        </TableCell>
                        <TableCell className="text-xs">{evaluation.label}</TableCell>
                        <TableCell className="text-xs">{evaluation.judge_model}</TableCell>
                        <TableCell className="text-xs">{truncateText(evaluation.comment || t.common.na, 50)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>

              <div className="flex items-center justify-between">
                <div className="text-sm text-muted-foreground">
                  {t.evaluations.showing} {evaluationsData.evaluations.length} {t.evaluations.of} {evaluationsData.total} {t.evaluations.evaluationsText}
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage(currentPage - 1)}
                    disabled={currentPage <= 1}
                  >
                    {t.evaluations.previous}
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage(currentPage + 1)}
                    disabled={currentPage >= evaluationsData.total_pages}
                  >
                    {t.evaluations.next}
                  </Button>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              {t.evaluations.noEvaluations}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
