from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
import json
import sqlite3
from uuid import uuid4

from app.models import (
    Concern,
    Questionnaire,
    RecommendationsResponse,
    SkinAnalysis,
    SkinLogResponse,
    WeeklyReport,
    XangiLatestSummary,
)


def create_skin_log(
    conn: sqlite3.Connection,
    questionnaire: Questionnaire,
    analysis: SkinAnalysis,
) -> str:
    skin_log_id = str(uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """
        INSERT INTO skin_logs
            (skin_log_id, created_at, questionnaire_json, analysis_json)
        VALUES (?, ?, ?, ?)
        """,
        (
            skin_log_id,
            created_at,
            json.dumps(questionnaire.model_dump(mode="json"), ensure_ascii=False),
            json.dumps(analysis.model_dump(mode="json"), ensure_ascii=False),
        ),
    )
    conn.commit()
    return skin_log_id


def update_recommendations(
    conn: sqlite3.Connection,
    skin_log_id: str,
    recommendations: RecommendationsResponse,
) -> None:
    conn.execute(
        "UPDATE skin_logs SET recommendation_json = ? WHERE skin_log_id = ?",
        (
            json.dumps(recommendations.model_dump(mode="json"), ensure_ascii=False),
            skin_log_id,
        ),
    )
    conn.commit()


def get_skin_log(conn: sqlite3.Connection, skin_log_id: str) -> SkinLogResponse | None:
    row = conn.execute(
        "SELECT * FROM skin_logs WHERE skin_log_id = ?",
        (skin_log_id,),
    ).fetchone()
    return _row_to_log(row) if row else None


def list_skin_logs(conn: sqlite3.Connection, limit: int = 50) -> list[SkinLogResponse]:
    rows = conn.execute(
        "SELECT * FROM skin_logs ORDER BY created_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return [_row_to_log(row) for row in rows]


def latest_skin_log(conn: sqlite3.Connection) -> SkinLogResponse | None:
    row = conn.execute(
        "SELECT * FROM skin_logs ORDER BY created_at DESC LIMIT 1",
    ).fetchone()
    return _row_to_log(row) if row else None


def build_latest_summary(log: SkinLogResponse | None) -> XangiLatestSummary:
    if log is None:
        return XangiLatestSummary(
            skin_log_id=None,
            created_at=None,
            summary="まだ肌ログがありません。",
            main_concerns=[],
            morning_care=[],
            night_care=[],
            buy_one=None,
        )

    recommendations = log.recommendations
    return XangiLatestSummary(
        skin_log_id=log.skin_log_id,
        created_at=log.created_at,
        summary=log.analysis.summary,
        main_concerns=log.analysis.detected_concerns,
        morning_care=recommendations.morning_care if recommendations else [],
        night_care=recommendations.night_care if recommendations else [],
        buy_one=(
            recommendations.buy_one.model_dump(mode="json")
            if recommendations
            else None
        ),
    )


def build_weekly_report(logs: list[SkinLogResponse], period_days: int = 7) -> WeeklyReport:
    since = datetime.now(timezone.utc) - timedelta(days=period_days)
    recent_logs = [
        log
        for log in logs
        if datetime.fromisoformat(log.created_at) >= since
    ]
    concern_counts: Counter[Concern] = Counter()
    for log in recent_logs:
        concern_counts.update(log.analysis.detected_concerns)

    frequent = [concern for concern, _ in concern_counts.most_common(3)]
    focus = _focus_for_concerns(frequent)
    if not recent_logs:
        trend_summary = "直近7日間の肌ログはまだありません。まずは1回記録すると週次レポートを作れます。"
    else:
        labels = "、".join(concern.value for concern in frequent) or "大きな偏りなし"
        trend_summary = f"直近{period_days}日間で{len(recent_logs)}件の記録があります。目立つテーマは{labels}です。"

    return WeeklyReport(
        period_days=period_days,
        log_count=len(recent_logs),
        trend_summary=trend_summary,
        frequent_concerns=frequent,
        recommended_focus=focus,
    )


def _row_to_log(row: sqlite3.Row) -> SkinLogResponse:
    recommendation_json = row["recommendation_json"]
    recommendations = (
        RecommendationsResponse.model_validate(json.loads(recommendation_json))
        if recommendation_json
        else None
    )
    return SkinLogResponse(
        skin_log_id=row["skin_log_id"],
        created_at=row["created_at"],
        questionnaire=Questionnaire.model_validate(json.loads(row["questionnaire_json"])),
        analysis=SkinAnalysis.model_validate(json.loads(row["analysis_json"])),
        recommendations=recommendations,
    )


def _focus_for_concerns(concerns: list[Concern]) -> list[str]:
    if not concerns:
        return ["写真と問診を1回記録する", "朝夜の基本ステップを固定する"]
    focus_map = {
        Concern.DRYNESS: "洗いすぎを避けて保湿量を安定させる",
        Concern.REDNESS: "赤みがある日は低刺激の保湿を優先する",
        Concern.PORES: "毛穴は洗顔と軽い保湿をセットで見る",
        Concern.SEBUM: "皮脂対策でも保湿を抜かない",
        Concern.DULLNESS: "朝のUV対策を抜かない",
        Concern.SENSITIVITY: "新規アイテムは一点ずつ試す",
    }
    return [focus_map[concern] for concern in concerns]

