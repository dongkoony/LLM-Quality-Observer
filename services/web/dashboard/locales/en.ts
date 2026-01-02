export const en = {
  // Navigation
  nav: {
    overview: "Overview",
    logs: "Logs",
    evaluations: "Evaluations",
    models: "Models",
  },

  // Overview page
  overview: {
    title: "Overview",
    subtitle: "Real-time monitoring of LLM quality metrics",
    welcome: "Welcome to LLM Quality Observer",
    welcomeDesc: "Monitor your LLM application's quality metrics in real-time. Navigate to Logs, Evaluations, or Models pages for detailed analysis.",
    totalLogs: "Total Logs",
    totalLogsDesc: "LLM request/response logs",
    evaluated: "Evaluated",
    evaluatedDesc: "Quality evaluated",
    avgLatency: "Avg Latency",
    avgLatencyDesc: "Response time",
    avgScore: "Avg Score",
    avgScoreDesc: "Quality rating (1-5)",
    qualityTrend: "Quality Score Trend (Last 30 Days)",
    latencyTrend: "Latency Trend (Last 30 Days)",
    volumeTrend: "Request Volume Trend (Last 30 Days)",
    recentActivity: "Recent Activity",
  },

  // Logs page
  logs: {
    title: "Logs",
    subtitle: "View all LLM request and response logs",
    tableTitle: "LLM Request Logs",
    id: "ID",
    createdAt: "Created At",
    userId: "User ID",
    prompt: "Prompt",
    response: "Response",
    model: "Model",
    latency: "Latency",
    status: "Status",
    showing: "Showing",
    of: "of",
    logsText: "logs",
    page: "Page",
    previous: "Previous",
    next: "Next",
    noLogs: "No logs found",
  },

  // Evaluations page
  evaluations: {
    title: "Evaluations",
    subtitle: "View LLM evaluation results and quality scores",
    tableTitle: "Quality Evaluations",
    total: "Total:",
    evaluationsText: "evaluations",
    id: "ID",
    createdAt: "Created At",
    logId: "Log ID",
    prompt: "Prompt",
    response: "Response",
    score: "Score",
    scoreInstruction: "Instruction",
    scoreTruthfulness: "Truthfulness",
    label: "Label",
    judge: "Judge",
    judgeType: "Judge Type",
    comment: "Comment",
    showing: "Showing",
    of: "of",
    page: "Page",
    previous: "Previous",
    next: "Next",
    noEvaluations: "No evaluations found",
    ruleBased: "Rule-Based",
    llmBased: "LLM Judge",
  },

  // Models page
  models: {
    title: "Models",
    subtitle: "Compare performance metrics across different LLM models",
    tableTitle: "Model Performance Comparison",
    modelVersion: "Model Version",
    totalRequests: "Total Requests",
    evaluatedCount: "Evaluated",
    avgLatency: "Avg Latency",
    avgScore: "Avg Score",
    evaluationRate: "Evaluation Rate",
    totalModels: "Total Models",
    totalModelsDesc: "Different models tracked",
    bestAvgScore: "Best Avg Score",
    bestAvgScoreDesc: "Highest quality rating",
    bestAvgLatency: "Best Avg Latency",
    bestAvgLatencyDesc: "Fastest response time",
    noModels: "No model data found",
  },

  // Common
  common: {
    loading: "Loading...",
    error: "Error:",
    na: "N/A",
  },
}

export type Translations = typeof en
