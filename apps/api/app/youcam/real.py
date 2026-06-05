from pathlib import Path
from typing import Any

import httpx

from app.models import Concern, Questionnaire, SkinAnalysis, SkinMetrics


class RealYouCamAdapter:
    def __init__(self, api_key: str, endpoint: str, timeout_sec: float) -> None:
        self._api_key = api_key
        self._endpoint = endpoint
        self._timeout_sec = timeout_sec

    async def analyze_image(
        self,
        image_path: Path,
        questionnaire: Questionnaire,
    ) -> SkinAnalysis:
        with image_path.open("rb") as image_file:
            async with httpx.AsyncClient(timeout=self._timeout_sec) as client:
                response = await client.post(
                    self._endpoint,
                    headers={"Authorization": f"Bearer {self._api_key}"},
                    files={"image": (image_path.name, image_file, "application/octet-stream")},
                    data={"questionnaire": questionnaire.model_dump_json()},
                )
        response.raise_for_status()
        return self._normalize(response.json(), questionnaire)

    def _normalize(self, payload: dict[str, Any], questionnaire: Questionnaire) -> SkinAnalysis:
        raw_metrics = payload.get("metrics", {}) if isinstance(payload, dict) else {}
        metrics = SkinMetrics(
            dryness=_as_score(raw_metrics.get("dryness"), 45),
            redness=_as_score(raw_metrics.get("redness"), 40),
            pores=_as_score(raw_metrics.get("pores"), 42),
            sebum=_as_score(raw_metrics.get("sebum"), 40),
            dullness=_as_score(raw_metrics.get("dullness"), 38),
            sensitivity=_as_score(raw_metrics.get("sensitivity"), 36),
        )
        detected = _detect_from_metrics(metrics, questionnaire)
        summary = payload.get("summary") if isinstance(payload, dict) else None
        return SkinAnalysis(
            source="youcam_real",
            summary=summary or "YouCam APIレスポンスをMVP用スキーマへ正規化しました。",
            metrics=metrics,
            detected_concerns=detected,
            advice_seed=["YouCam実レスポンス由来の指標を元に推薦を作成します。"],
            risk_notes=[],
        )


def _as_score(raw: Any, default: int) -> int:
    try:
        value = int(float(raw))
    except (TypeError, ValueError):
        value = default
    return max(0, min(100, value))


def _detect_from_metrics(metrics: SkinMetrics, questionnaire: Questionnaire) -> list[Concern]:
    mapping = {
        Concern.DRYNESS: metrics.dryness,
        Concern.REDNESS: metrics.redness,
        Concern.PORES: metrics.pores,
        Concern.SEBUM: metrics.sebum,
        Concern.DULLNESS: metrics.dullness,
        Concern.SENSITIVITY: metrics.sensitivity,
    }
    detected = [concern for concern, score in mapping.items() if score >= 58]
    for concern in questionnaire.concerns:
        if concern not in detected:
            detected.append(concern)
    return detected or [Concern.DRYNESS]

