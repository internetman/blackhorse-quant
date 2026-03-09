export type UserRole = 'admin' | 'leader' | 'member';
export type ActionType = '可交易' | '观望' | '不建议交易' | '风险升高';
export type BiasType = '偏低吸' | '偏突破' | '偏减仓' | '暂不参与';
export type ConfidenceLevel = '高' | '中' | '低';
export type PositionLevel = '空仓' | '轻仓' | '中仓' | '重仓';
export type ReviewType = 'T+1' | 'T+3' | 'T+5';
export type VerdictType = '有效' | '一般' | '失效';

export interface User {
  id: string;
  username: string;
  nickname: string;
  role: UserRole;
  joinedAt: string;
  isActive: boolean;
}

export interface Circle {
  id: string;
  name: string;
  memberCount: number;
}

export interface WatchItem {
  id: string;
  userId: string;
  symbol: string;
  name: string;
  reason: string;
  addedAt: string;
  isActive: boolean;
}

export interface StockSearchItem {
  symbol: string;
  name: string;
}

export interface Recommendation {
  id: string;
  symbol: string;
  name: string;
  date: string;
  action: ActionType;
  bias: BiasType;
  confidence: ConfidenceLevel;
  pricePlan: string;
  summary: string;
  reasons: string[];
  risks: string[];
  invalidCondition: string;
  reviewAt: ReviewType;
  generatedAt: string;
}

export interface DailySummary {
  total: number;
  tradable: number;
  watch: number;
  risky: number;
}

export interface Review {
  id: string;
  recommendationId: string;
  symbol: string;
  name: string;
  reviewType: ReviewType;
  reviewDate: string;
  originalAction: ActionType;
  originalSummary: string;
  priceAtRecommend: number;
  priceAtReview: number;
  priceChange: string;
  verdict: VerdictType;
  explanation: string;
  generatedAt: string;
}

export interface ReviewStats {
  total: number;
  effective: number;
  neutral: number;
  ineffective: number;
  effectiveRate: number;
}

export interface PrivatePosition {
  id: string;
  userId: string;
  symbol: string;
  name: string;
  level: PositionLevel;
  costPrice: number | null;
  notes: string;
  updatedAt: string;
}

export interface RecommendationsResponse {
  date: string;
  summary: DailySummary;
  recommendations: Recommendation[];
}
