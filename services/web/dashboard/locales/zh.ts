import { Translations } from "./en"

export const zh: Translations = {
  // Navigation
  nav: {
    overview: "概览",
    logs: "日志",
    evaluations: "评估",
    models: "模型",
  },

  // Overview page
  overview: {
    title: "概览",
    subtitle: "LLM质量指标实时监控",
    welcome: "欢迎使用LLM Quality Observer",
    welcomeDesc: "实时监控您的LLM应用程序的质量指标。导航到日志、评估或模型页面以查看详细分析。",
    totalLogs: "总日志数",
    totalLogsDesc: "LLM请求/响应日志",
    evaluated: "已评估",
    evaluatedDesc: "质量已评估",
    avgLatency: "平均延迟",
    avgLatencyDesc: "响应时间",
    avgScore: "平均分数",
    avgScoreDesc: "质量评分 (1-5)",
    qualityTrend: "质量分数趋势（最近30天）",
    latencyTrend: "延迟趋势（最近30天）",
    volumeTrend: "请求量趋势（最近30天）",
    recentActivity: "最近活动",
  },

  // Logs page
  logs: {
    title: "日志",
    subtitle: "查看所有LLM请求和响应日志",
    tableTitle: "LLM请求日志",
    id: "ID",
    createdAt: "创建时间",
    userId: "用户ID",
    prompt: "提示",
    response: "响应",
    model: "模型",
    latency: "延迟",
    status: "状态",
    showing: "显示",
    of: "/",
    logsText: "日志",
    page: "页",
    previous: "上一页",
    next: "下一页",
    noLogs: "未找到日志",
  },

  // Evaluations page
  evaluations: {
    title: "评估",
    subtitle: "查看LLM评估结果和质量分数",
    tableTitle: "质量评估",
    total: "总计:",
    evaluationsText: "评估",
    id: "ID",
    createdAt: "创建时间",
    logId: "日志ID",
    prompt: "提示",
    response: "响应",
    score: "分数",
    label: "标签",
    judge: "评审员",
    comment: "评论",
    showing: "显示",
    of: "/",
    page: "页",
    previous: "上一页",
    next: "下一页",
    noEvaluations: "未找到评估",
  },

  // Models page
  models: {
    title: "模型",
    subtitle: "比较不同LLM模型的性能指标",
    tableTitle: "模型性能比较",
    modelVersion: "模型版本",
    totalRequests: "总请求数",
    evaluatedCount: "评估数",
    avgLatency: "平均延迟",
    avgScore: "平均分数",
    evaluationRate: "评估率",
    totalModels: "总模型数",
    totalModelsDesc: "跟踪的模型数",
    bestAvgScore: "最佳平均分数",
    bestAvgScoreDesc: "最高质量评分",
    bestAvgLatency: "最佳平均延迟",
    bestAvgLatencyDesc: "最快响应时间",
    noModels: "未找到模型数据",
  },

  // Common
  common: {
    loading: "加载中...",
    error: "错误:",
    na: "N/A",
  },
}
