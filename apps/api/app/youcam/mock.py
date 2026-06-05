from pathlib import Path

from app.models import Concern, Questionnaire, SkinAnalysis, SkinMetrics


class MockYouCamAdapter:
    async def analyze_image(
        self,
        image_path: Path,
        questionnaire: Questionnaire,
    ) -> SkinAnalysis:
        file_bump = image_path.stat().st_size % 9 if image_path.exists() else 0
        scores = {
            Concern.DRYNESS: 38,
            Concern.REDNESS: 34,
            Concern.PORES: 36,
            Concern.SEBUM: 35,
            Concern.DULLNESS: 33,
            Concern.SENSITIVITY: 32,
        }

        requested = set(questionnaire.concerns)
        for concern in requested:
            scores[concern] = 68 + file_bump

        if Concern.DRYNESS in requested and Concern.SENSITIVITY in requested:
            scores[Concern.REDNESS] = max(scores[Concern.REDNESS], 57)
        if Concern.SEBUM in requested:
            scores[Concern.PORES] = max(scores[Concern.PORES], 61)
        if not requested:
            scores[Concern.DRYNESS] = 55 + file_bump
            scores[Concern.DULLNESS] = 52

        detected = [
            concern
            for concern, score in scores.items()
            if score >= 58 or concern in requested
        ]
        if not detected:
            detected = [Concern.DRYNESS]

        labels = "、".join(concern.value for concern in detected[:3])
        summary = f"mock診断では、今の優先テーマは{labels}です。洗いすぎを避け、保湿とUVを軸に整えます。"

        return SkinAnalysis(
            source="youcam_mock",
            summary=summary,
            metrics=SkinMetrics(
                dryness=_clamp(scores[Concern.DRYNESS]),
                redness=_clamp(scores[Concern.REDNESS]),
                pores=_clamp(scores[Concern.PORES]),
                sebum=_clamp(scores[Concern.SEBUM]),
                dullness=_clamp(scores[Concern.DULLNESS]),
                sensitivity=_clamp(scores[Concern.SENSITIVITY]),
            ),
            detected_concerns=detected,
            advice_seed=[
                "朝は短くても保湿とUVを残す",
                "夜はこすらず落として保護する",
                "買い足しは不足役割を1つだけに絞る",
            ],
            risk_notes=["mock結果です。実際のYouCam API仕様はadapter層で差し替えます。"],
        )


def _clamp(value: int) -> int:
    return max(0, min(100, value))

