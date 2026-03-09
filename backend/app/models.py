from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import date


ActionType = Literal["可交易", "观望", "不建议交易", "风险升高"]
BiasType = Literal["偏低吸", "偏突破", "偏减仓", "暂不参与"]
ConfidenceLevel = Literal["高", "中", "低"]
PositionLevel = Literal["空仓", "轻仓", "中仓", "重仓"]
ReviewType = Literal["T+1", "T+3", "T+5"]
VerdictType = Literal["有效", "一般", "失效"]
UserRole = Literal["admin", "leader", "member"]


class User(BaseModel):
    id: str
    username: str = ""
    nickname: str
    role: UserRole = "member"
    joinedAt: str = ""
    isActive: bool = True


class Circle(BaseModel):
    id: str
    name: str
    memberCount: int = 0


class WatchItem(BaseModel):
    id: str
    userId: str
    symbol: str
    name: str
    reason: str = ""
    addedAt: str = ""
    isActive: bool = True


class Recommendation(BaseModel):
    id: str
    symbol: str
    name: str
    date: str
    action: ActionType
    bias: BiasType
    confidence: ConfidenceLevel
    pricePlan: str
    summary: str
    reasons: list[str] = []
    risks: list[str] = []
    invalidCondition: str = ""
    reviewAt: ReviewType = "T+1"
    generatedAt: str = ""
    quote: Optional["QuoteData"] = None
    news: list["NewsItem"] = Field(default_factory=list)


class DailySummary(BaseModel):
    total: int = 0
    tradable: int = 0
    watch: int = 0
    risky: int = 0


class RecommendationsResponse(BaseModel):
    date: str
    summary: DailySummary
    recommendations: list[Recommendation]


class Review(BaseModel):
    id: str
    userId: str
    recommendationId: str
    symbol: str
    name: str
    reviewType: ReviewType
    reviewDate: str
    originalAction: ActionType
    originalSummary: str
    priceAtRecommend: float
    priceAtReview: float
    priceChange: str
    verdict: VerdictType
    explanation: str
    generatedAt: str = ""


class ReviewStats(BaseModel):
    total: int = 0
    effective: int = 0
    neutral: int = 0
    ineffective: int = 0
    effectiveRate: float = 0.0


class QuoteData(BaseModel):
    symbol: str
    latestPrice: float
    changePercent: float
    volume: int
    updatedAt: str


class NewsItem(BaseModel):
    title: str
    date: str
    summary: str = ""


class PrivatePosition(BaseModel):
    id: str
    userId: str
    symbol: str
    name: str
    level: PositionLevel = "空仓"
    costPrice: Optional[float] = None
    notes: str = ""
    updatedAt: str = ""


class LoginRequest(BaseModel):
    username: str
    password: str


class CreateUserRequest(BaseModel):
    username: str
    password: str
    nickname: str
    role: UserRole = "member"


class RoleUpdateRequest(BaseModel):
    role: UserRole
