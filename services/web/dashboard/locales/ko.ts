import { Translations } from "./en"

export const ko: Translations = {
  // Navigation
  nav: {
    overview: "개요",
    logs: "로그",
    evaluations: "평가",
    models: "모델",
  },

  // Overview page
  overview: {
    title: "개요",
    subtitle: "LLM 품질 지표 실시간 모니터링",
    welcome: "LLM Quality Observer에 오신 것을 환영합니다",
    welcomeDesc: "LLM 애플리케이션의 품질 지표를 실시간으로 모니터링하세요. 로그, 평가, 모델 페이지에서 자세한 분석을 확인할 수 있습니다.",
    totalLogs: "총 로그 수",
    totalLogsDesc: "LLM 요청/응답 로그",
    evaluated: "평가 완료",
    evaluatedDesc: "품질 평가 완료",
    avgLatency: "평균 지연시간",
    avgLatencyDesc: "응답 시간",
    avgScore: "평균 점수",
    avgScoreDesc: "품질 평가 (1-5)",
    qualityTrend: "품질 점수 추이 (최근 30일)",
    latencyTrend: "지연시간 추이 (최근 30일)",
    volumeTrend: "요청 수 추이 (최근 30일)",
    recentActivity: "최근 활동",
  },

  // Logs page
  logs: {
    title: "로그",
    subtitle: "모든 LLM 요청 및 응답 로그 조회",
    tableTitle: "LLM 요청 로그",
    id: "ID",
    createdAt: "생성 시각",
    userId: "사용자 ID",
    prompt: "프롬프트",
    response: "응답",
    model: "모델",
    latency: "지연시간",
    status: "상태",
    showing: "표시 중",
    of: "/",
    logsText: "로그",
    page: "페이지",
    previous: "이전",
    next: "다음",
    noLogs: "로그가 없습니다",
  },

  // Evaluations page
  evaluations: {
    title: "평가",
    subtitle: "LLM 평가 결과 및 품질 점수 조회",
    tableTitle: "품질 평가",
    total: "총:",
    evaluationsText: "평가",
    id: "ID",
    createdAt: "생성 시각",
    logId: "로그 ID",
    prompt: "프롬프트",
    response: "응답",
    score: "점수",
    scoreInstruction: "지시 준수",
    scoreTruthfulness: "정확성",
    label: "레이블",
    judge: "평가자",
    judgeType: "평가 방식",
    comment: "코멘트",
    showing: "표시 중",
    of: "/",
    page: "페이지",
    previous: "이전",
    next: "다음",
    noEvaluations: "평가가 없습니다",
    ruleBased: "룰 기반",
    llmBased: "LLM 평가",
  },

  // Models page
  models: {
    title: "모델",
    subtitle: "다양한 LLM 모델의 성능 지표 비교",
    tableTitle: "모델 성능 비교",
    modelVersion: "모델 버전",
    totalRequests: "총 요청 수",
    evaluatedCount: "평가 수",
    avgLatency: "평균 지연시간",
    avgScore: "평균 점수",
    evaluationRate: "평가율",
    totalModels: "총 모델 수",
    totalModelsDesc: "추적 중인 모델 수",
    bestAvgScore: "최고 평균 점수",
    bestAvgScoreDesc: "가장 높은 품질 평가",
    bestAvgLatency: "최단 평균 지연시간",
    bestAvgLatencyDesc: "가장 빠른 응답 시간",
    noModels: "모델 데이터가 없습니다",
  },

  // Common
  common: {
    loading: "로딩 중...",
    error: "오류:",
    na: "N/A",
  },
}
