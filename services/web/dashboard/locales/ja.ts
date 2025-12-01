import { Translations } from "./en"

export const ja: Translations = {
  // Navigation
  nav: {
    overview: "概要",
    logs: "ログ",
    evaluations: "評価",
    models: "モデル",
  },

  // Overview page
  overview: {
    title: "概要",
    subtitle: "LLM品質メトリクスのリアルタイム監視",
    welcome: "LLM Quality Observerへようこそ",
    welcomeDesc: "LLMアプリケーションの品質メトリクスをリアルタイムで監視します。ログ、評価、モデルページで詳細な分析を確認できます。",
    totalLogs: "総ログ数",
    totalLogsDesc: "LLMリクエスト/レスポンスログ",
    evaluated: "評価済み",
    evaluatedDesc: "品質評価済み",
    avgLatency: "平均レイテンシ",
    avgLatencyDesc: "応答時間",
    avgScore: "平均スコア",
    avgScoreDesc: "品質評価 (1-5)",
    qualityTrend: "品質スコア推移 (過去30日)",
    latencyTrend: "レイテンシ推移 (過去30日)",
    volumeTrend: "リクエスト数推移 (過去30日)",
    recentActivity: "最近のアクティビティ",
  },

  // Logs page
  logs: {
    title: "ログ",
    subtitle: "すべてのLLMリクエストとレスポンスログを表示",
    tableTitle: "LLMリクエストログ",
    id: "ID",
    createdAt: "作成日時",
    userId: "ユーザーID",
    prompt: "プロンプト",
    response: "レスポンス",
    model: "モデル",
    latency: "レイテンシ",
    status: "ステータス",
    showing: "表示中",
    of: "/",
    logsText: "ログ",
    page: "ページ",
    previous: "前へ",
    next: "次へ",
    noLogs: "ログが見つかりません",
  },

  // Evaluations page
  evaluations: {
    title: "評価",
    subtitle: "LLM評価結果と品質スコアを表示",
    tableTitle: "品質評価",
    total: "合計:",
    evaluationsText: "評価",
    id: "ID",
    createdAt: "作成日時",
    logId: "ログID",
    prompt: "プロンプト",
    response: "レスポンス",
    score: "スコア",
    label: "ラベル",
    judge: "評価者",
    comment: "コメント",
    showing: "表示中",
    of: "/",
    page: "ページ",
    previous: "前へ",
    next: "次へ",
    noEvaluations: "評価が見つかりません",
  },

  // Models page
  models: {
    title: "モデル",
    subtitle: "異なるLLMモデルのパフォーマンスメトリクスを比較",
    tableTitle: "モデルパフォーマンス比較",
    modelVersion: "モデルバージョン",
    totalRequests: "総リクエスト数",
    evaluatedCount: "評価数",
    avgLatency: "平均レイテンシ",
    avgScore: "平均スコア",
    evaluationRate: "評価率",
    totalModels: "総モデル数",
    totalModelsDesc: "追跡中のモデル数",
    bestAvgScore: "最高平均スコア",
    bestAvgScoreDesc: "最高品質評価",
    bestAvgLatency: "最短平均レイテンシ",
    bestAvgLatencyDesc: "最速応答時間",
    noModels: "モデルデータが見つかりません",
  },

  // Common
  common: {
    loading: "読み込み中...",
    error: "エラー:",
    na: "N/A",
  },
}
