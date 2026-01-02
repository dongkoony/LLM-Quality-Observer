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
import { getLogs } from "@/lib/api"
import type { LogListResponse } from "@/lib/types"
import { useTranslations } from "@/lib/use-translations"

export default function LogsContent() {
  const t = useTranslations()
  const [logsData, setLogsData] = useState<LogListResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [currentPage, setCurrentPage] = useState(1)
  const pageSize = 10

  useEffect(() => {
    async function fetchLogs() {
      try {
        setLoading(true)
        const data = await getLogs(currentPage, pageSize)
        setLogsData(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to fetch logs")
      } finally {
        setLoading(false)
      }
    }

    fetchLogs()
  }, [currentPage])

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString()
  }

  const truncateText = (text: string, maxLength: number = 100) => {
    if (text.length <= maxLength) return text
    return text.substring(0, maxLength) + "..."
  }

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">{t.logs.title}</h1>
        <p className="text-muted-foreground">
          {t.logs.subtitle}
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
            <CardTitle>{t.logs.tableTitle}</CardTitle>
            <div className="text-sm text-muted-foreground">
              {logsData && `${logsData.total} ${t.logs.logsText} | ${t.logs.page} ${logsData.page} ${t.logs.of} ${logsData.total_pages}`}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8">{t.common.loading}</div>
          ) : logsData && logsData.logs.length > 0 ? (
            <div className="space-y-4">
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-[80px]">{t.logs.id}</TableHead>
                      <TableHead className="w-[180px]">{t.logs.createdAt}</TableHead>
                      <TableHead className="w-[100px]">{t.logs.userId}</TableHead>
                      <TableHead>{t.logs.prompt}</TableHead>
                      <TableHead>{t.logs.response}</TableHead>
                      <TableHead className="w-[120px]">{t.logs.model}</TableHead>
                      <TableHead className="w-[100px]">{t.logs.latency}</TableHead>
                      <TableHead className="w-[80px]">{t.logs.status}</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {logsData.logs.map((log) => (
                      <TableRow key={log.id}>
                        <TableCell className="font-medium">{log.id}</TableCell>
                        <TableCell className="text-xs">{formatDate(log.created_at)}</TableCell>
                        <TableCell className="text-xs">{log.user_id || t.common.na}</TableCell>
                        <TableCell className="text-xs">{truncateText(log.prompt, 80)}</TableCell>
                        <TableCell className="text-xs">{truncateText(log.response, 80)}</TableCell>
                        <TableCell className="text-xs">{log.model_version || t.common.na}</TableCell>
                        <TableCell className="text-xs">
                          {log.latency_ms ? `${(log.latency_ms / 1000).toFixed(2)}s` : t.common.na}
                        </TableCell>
                        <TableCell>
                          <span
                            className={`text-xs px-2 py-1 rounded ${
                              log.status === "success"
                                ? "bg-green-100 text-green-800"
                                : "bg-red-100 text-red-800"
                            }`}
                          >
                            {log.status}
                          </span>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>

              <div className="flex items-center justify-between">
                <div className="text-sm text-muted-foreground">
                  {t.logs.showing} {logsData.logs.length} {t.logs.of} {logsData.total} {t.logs.logsText}
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage(currentPage - 1)}
                    disabled={currentPage <= 1}
                  >
                    {t.logs.previous}
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage(currentPage + 1)}
                    disabled={currentPage >= logsData.total_pages}
                  >
                    {t.logs.next}
                  </Button>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              {t.logs.noLogs}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
