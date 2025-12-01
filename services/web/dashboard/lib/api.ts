import type {
  DashboardSummary,
  LogListResponse,
  EvaluationListResponse,
  ModelStatsResponse,
} from "./types"

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:18000"

async function fetchAPI<T>(endpoint: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`)

  if (!response.ok) {
    throw new Error(`API Error: ${response.statusText}`)
  }

  return response.json()
}

/**
 * Get dashboard summary statistics
 */
export async function getDashboardSummary(): Promise<DashboardSummary> {
  return fetchAPI<DashboardSummary>("/api/dashboard/summary")
}

/**
 * Get paginated list of LLM logs
 */
export async function getLogs(
  page: number = 1,
  pageSize: number = 20
): Promise<LogListResponse> {
  return fetchAPI<LogListResponse>(
    `/api/dashboard/logs?page=${page}&page_size=${pageSize}`
  )
}

/**
 * Get paginated list of evaluations
 */
export async function getEvaluations(
  page: number = 1,
  pageSize: number = 20
): Promise<EvaluationListResponse> {
  return fetchAPI<EvaluationListResponse>(
    `/api/dashboard/evaluations?page=${page}&page_size=${pageSize}`
  )
}

/**
 * Get model statistics
 */
export async function getModelStats(): Promise<ModelStatsResponse> {
  return fetchAPI<ModelStatsResponse>("/api/dashboard/models/stats")
}
