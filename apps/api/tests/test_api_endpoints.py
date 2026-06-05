import asyncio
from io import BytesIO
import json
from pathlib import Path

from fastapi import UploadFile

from app.config import Settings
from app.db.database import connect, init_db
from app.main import (
    analyze_skin,
    create_recommendations,
    get_latest_log_summary,
    get_weekly_report,
)
from app.models import RecommendationRequest


def test_mock_analyze_recommend_and_xangi_summaries(tmp_path: Path) -> None:
    db_path = tmp_path / "skin_care.db"
    upload_dir = tmp_path / "uploads"
    init_db(db_path)
    conn = connect(db_path)
    try:
        settings = Settings(
            database_path=db_path,
            upload_dir=upload_dir,
            youcam_mode="mock",
        )
        questionnaire = {
            "concerns": ["乾燥", "敏感"],
            "budget_yen": 2000,
            "morning_minutes": 5,
            "current_items": ["洗顔", "化粧水"],
        }
        image = UploadFile(
            file=BytesIO(b"mock image bytes"),
            filename="face.jpg",
        )

        analyzed = asyncio.run(
            analyze_skin(
                questionnaire=json.dumps(questionnaire, ensure_ascii=False),
                image=image,
                settings=settings,
                conn=conn,
            )
        )
        assert analyzed.image_deleted is True
        assert analyzed.analysis.source == "youcam_mock"
        assert not any(upload_dir.glob("*"))

        recommendation = create_recommendations(
            RecommendationRequest(skin_log_id=analyzed.skin_log_id),
            conn=conn,
        )
        assert recommendation.buy_one.product_id in {
            "ceramide_lotion",
            "barrier_cream",
            "uv_milk",
        }

        latest = get_latest_log_summary(conn=conn)
        assert latest.skin_log_id == analyzed.skin_log_id
        assert "image" not in latest.model_dump_json().lower()

        weekly = get_weekly_report(conn=conn)
        assert weekly.log_count == 1
    finally:
        conn.close()

