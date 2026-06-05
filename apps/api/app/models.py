from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Concern(str, Enum):
    DRYNESS = "乾燥"
    REDNESS = "赤み"
    PORES = "毛穴"
    SEBUM = "皮脂"
    DULLNESS = "くすみ"
    SENSITIVITY = "敏感"


class Questionnaire(BaseModel):
    concerns: list[Concern] = Field(default_factory=list)
    budget_yen: int = Field(ge=0, le=100_000)
    morning_minutes: int = Field(ge=0, le=120)
    current_items: list[str] = Field(default_factory=list, max_length=20)


class SkinMetrics(BaseModel):
    dryness: int = Field(ge=0, le=100)
    redness: int = Field(ge=0, le=100)
    pores: int = Field(ge=0, le=100)
    sebum: int = Field(ge=0, le=100)
    dullness: int = Field(ge=0, le=100)
    sensitivity: int = Field(ge=0, le=100)


class SkinAnalysis(BaseModel):
    source: str
    summary: str
    metrics: SkinMetrics
    detected_concerns: list[Concern]
    advice_seed: list[str] = Field(default_factory=list)
    risk_notes: list[str] = Field(default_factory=list)


class AnalyzeResponse(BaseModel):
    skin_log_id: str
    analysis: SkinAnalysis
    image_deleted: bool = True


class ProductRecord(BaseModel):
    product_id: str
    name: str
    brand: str
    category: str
    price_yen: int
    concerns: list[str]
    tags: list[str]
    description: str


class ProductCandidate(BaseModel):
    product_id: str
    name: str
    brand: str
    category: str
    price_yen: int
    match_score: float
    reasons: list[str]


class RecommendationRequest(BaseModel):
    skin_log_id: str | None = None
    questionnaire: Questionnaire | None = None
    analysis: SkinAnalysis | None = None


class RecommendationsResponse(BaseModel):
    skin_log_id: str | None = None
    care_policy: str
    morning_care: list[str]
    night_care: list[str]
    buy_one: ProductCandidate
    products: list[ProductCandidate]
    memo_refs: list[str] = Field(default_factory=list)
    disclaimer: str = "医療診断ではなく、美容上の一般的なアドバイスです。強い症状がある場合は専門家へ相談してください。"


class SkinLogResponse(BaseModel):
    skin_log_id: str
    created_at: str
    questionnaire: Questionnaire
    analysis: SkinAnalysis
    recommendations: RecommendationsResponse | None = None


class XangiLatestSummary(BaseModel):
    skin_log_id: str | None
    created_at: str | None
    summary: str
    main_concerns: list[Concern]
    morning_care: list[str]
    night_care: list[str]
    buy_one: dict[str, Any] | None
    privacy_note: str = "顔写真、画像URL、個人を特定する情報は含みません。"


class WeeklyReport(BaseModel):
    period_days: int
    log_count: int
    trend_summary: str
    frequent_concerns: list[Concern]
    recommended_focus: list[str]
    privacy_note: str = "Discord/xangi共有用に、画像や個人情報は除外しています。"

