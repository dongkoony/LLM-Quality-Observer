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

export default function EvaluationsContent() {
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
        <h1 className="text-3xl font-bold tracking-tight">Evaluations</h1>
        <p className="text-muted-foreground">
          View LLM evaluation results and quality scores
        </p>
      </div>

      {error && (
        <Card className="border-red-500">
          <CardContent className="pt-6">
            <p className="text-sm text-red-500">Error: {error}</p>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Quality Evaluations</CardTitle>
            <div className="text-sm text-muted-foreground">
              {evaluationsData && `Total: ${evaluationsData.total} evaluations | Page ${evaluationsData.page} of ${evaluationsData.total_pages}`}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8">Loading...</div>
          ) : evaluationsData && evaluationsData.evaluations.length > 0 ? (
            <div className="space-y-4">
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-[60px]">ID</TableHead>
                      <TableHead className="w-[140px]">Created At</TableHead>
                      <TableHead className="w-[80px]">Log ID</TableHead>
                      <TableHead>Prompt</TableHead>
                      <TableHead>Response</TableHead>
                      <TableHead className="w-[80px]">Score</TableHead>
                      <TableHead className="w-[80px]">Label</TableHead>
                      <TableHead className="w-[100px]">Judge</TableHead>
                      <TableHead>Comment</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {evaluationsData.evaluations.map((evaluation) => (
                      <TableRow key={evaluation.id}>
                        <TableCell className="font-medium">{evaluation.id}</TableCell>
                        <TableCell className="text-xs">{formatDate(evaluation.created_at)}</TableCell>
                        <TableCell className="text-xs">{evaluation.log_id}</TableCell>
                        <TableCell className="text-xs">{truncateText(evaluation.log_prompt || "N/A", 60)}</TableCell>
                        <TableCell className="text-xs">{truncateText(evaluation.log_response || "N/A", 60)}</TableCell>
                        <TableCell>
                          <span className={`text-xs px-2 py-1 rounded ${getScoreColor(evaluation.overall_score)}`}>
                            {evaluation.overall_score}/5
                          </span>
                        </TableCell>
                        <TableCell className="text-xs">{evaluation.label}</TableCell>
                        <TableCell className="text-xs">{evaluation.judge_model}</TableCell>
                        <TableCell className="text-xs">{truncateText(evaluation.comment || "N/A", 50)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>

              <div className="flex items-center justify-between">
                <div className="text-sm text-muted-foreground">
                  Showing {evaluationsData.evaluations.length} of {evaluationsData.total} evaluations
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage(currentPage - 1)}
                    disabled={currentPage <= 1}
                  >
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage(currentPage + 1)}
                    disabled={currentPage >= evaluationsData.total_pages}
                  >
                    Next
                  </Button>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              No evaluations found
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
