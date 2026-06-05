from __future__ import annotations

from app.models import (
    Concern,
    ProductCandidate,
    Questionnaire,
    RecommendationsResponse,
    SkinAnalysis,
)
from app.rag.base import Retriever


class RecommendationService:
    def __init__(self, retriever: Retriever) -> None:
        self._retriever = retriever

    def build(
        self,
        questionnaire: Questionnaire,
        analysis: SkinAnalysis,
        skin_log_id: str | None = None,
    ) -> RecommendationsResponse:
        concerns = _merge_concerns(questionnaire, analysis)
        query = " ".join(concern.value for concern in concerns)
        products = self._retriever.retrieve_products(
            query=query,
            concerns=concerns,
            budget_yen=questionnaire.budget_yen,
            limit=8,
        )
        candidates = [
            _score_product(product, questionnaire, analysis, concerns)
            for product in products
        ]
        candidates.sort(key=lambda item: item.match_score, reverse=True)
        if not candidates:
            raise ValueError("product DB is empty; recommendation cannot be generated")

        top_products = candidates[:3]
        buy_one = top_products[0]
        return RecommendationsResponse(
            skin_log_id=skin_log_id,
            care_policy=_care_policy(concerns),
            morning_care=_morning_care(concerns, questionnaire.morning_minutes),
            night_care=_night_care(concerns),
            buy_one=buy_one,
            products=top_products,
            memo_refs=self._retriever.retrieve_memos(concerns, limit=3),
        )


def _merge_concerns(
    questionnaire: Questionnaire,
    analysis: SkinAnalysis,
) -> list[Concern]:
    merged: list[Concern] = []
    for concern in [*analysis.detected_concerns, *questionnaire.concerns]:
        if concern not in merged:
            merged.append(concern)
    return merged or [Concern.DRYNESS]


def _score_product(
    product,
    questionnaire: Questionnaire,
    analysis: SkinAnalysis,
    concerns: list[Concern],
) -> ProductCandidate:
    target = {concern.value for concern in concerns}
    product_concerns = set(product.concerns)
    matched = sorted(product_concerns & target)

    score = 20.0 + 24.0 * len(matched)
    if questionnaire.budget_yen == 0:
        score += 5.0
    elif product.price_yen <= questionnaire.budget_yen:
        score += 18.0
    else:
        score -= min(18.0, (product.price_yen - questionnaire.budget_yen) / 300)

    metrics = analysis.metrics
    if metrics.dryness >= 60 and "乾燥" in product_concerns:
        score += 8.0
    if metrics.redness >= 55 and "赤み" in product_concerns:
        score += 8.0
    if metrics.sensitivity >= 55 and "敏感" in product_concerns:
        score += 8.0
    if metrics.sebum >= 60 and "皮脂" in product_concerns:
        score += 6.0
    if metrics.pores >= 60 and "毛穴" in product_concerns:
        score += 6.0
    if metrics.dullness >= 55 and "くすみ" in product_concerns:
        score += 6.0
    if questionnaire.morning_minutes <= 5 and ("時短" in product.tags or product.category in {"日焼け止め", "ジェル"}):
        score += 4.0

    reasons = [f"{label}の悩みに合う" for label in matched[:3]]
    if questionnaire.budget_yen and product.price_yen <= questionnaire.budget_yen:
        reasons.append("予算内で試しやすい")
    if not reasons:
        reasons.append("基本ケアに組み込みやすい")

    return ProductCandidate(
        product_id=product.product_id,
        name=product.name,
        brand=product.brand,
        category=product.category,
        price_yen=product.price_yen,
        match_score=round(score, 1),
        reasons=reasons,
    )


def _care_policy(concerns: list[Concern]) -> str:
    labels = {concern.value for concern in concerns}
    if {"乾燥", "敏感", "赤み"} & labels:
        return "まずはバリアを整える方針です。攻めの美容液を増やすより、低刺激の保湿と保護を優先します。"
    if {"皮脂", "毛穴"} & labels:
        return "落とすケアを強くしすぎず、皮脂を取りすぎない洗顔と軽い保湿でバランスを取ります。"
    if "くすみ" in labels:
        return "朝のUV対策と保湿を固定し、透明感ケアは続けやすい一点追加に絞ります。"
    return "手持ちアイテムを活かし、朝夜の基本ステップを続けやすく整えます。"


def _morning_care(concerns: list[Concern], morning_minutes: int) -> list[str]:
    labels = {concern.value for concern in concerns}
    steps = ["ぬるま湯または低刺激洗顔で軽く整える", "化粧水または軽い保湿でうるおいを入れる"]
    if {"乾燥", "敏感", "赤み"} & labels:
        steps.append("乾燥しやすい部分だけクリームを薄く重ねる")
    if {"皮脂", "毛穴"} & labels:
        steps.append("べたつく部分は薄く、頬は保湿を残す")
    steps.append("日焼け止めで仕上げる")
    if morning_minutes <= 5:
        return ["洗顔は短時間にしてこすらない", "保湿と日焼け止めを優先する"]
    return steps


def _night_care(concerns: list[Concern]) -> list[str]:
    labels = {concern.value for concern in concerns}
    steps = ["メイクや日焼け止めをこすらず落とす", "化粧水で水分を補う"]
    if {"乾燥", "赤み", "敏感"} & labels:
        steps.append("セラミド系の保湿でバリアを支える")
    if {"毛穴", "皮脂"} & labels:
        steps.append("皮脂が多い部分だけ洗顔を丁寧にし、保湿は抜かない")
    steps.append("クリームまたはジェルで仕上げる")
    return steps

