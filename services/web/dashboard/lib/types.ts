// API Response Types

export interface DashboardSummary {
  total_logs: number
  total_evaluated: number
  avg_latency_ms: number | null
  avg_score: number | null
}

export interface LogItem {
  id: number
  created_at: string
  user_id: string | null
  prompt: string
  response: string
  model_version: string | null
  latency_ms: number | null
  status: string
}

export interface LogListResponse {
  logs: LogItem[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface EvaluationItem {
  id: number
  created_at: string
  log_id: number
  overall_score: number
  is_flagged: boolean
  label: string
  judge_model: string
  comment: string | null
  log_prompt: string | null
  log_response: string | null
  log_model_version: string | null
}

export interface EvaluationListResponse {
  evaluations: EvaluationItem[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface ModelStats {
  model_version: string
  total_requests: number
  avg_latency_ms: number | null
  avg_score: number | null
  total_evaluated: number
}

export interface ModelStatsResponse {
  models: ModelStats[]
}

export interface TimeSeriesDataPoint {
  date: string // YYYY-MM-DD format
  avg_score: number | null
  avg_latency_ms: number | null
  total_requests: number
  total_evaluated: number
}

export interface TimeSeriesResponse {
  data: TimeSeriesDataPoint[]
}
