from pathlib import Path

from app.db.database import connect, init_db
from app.models import Concern, Questionnaire, SkinAnalysis, SkinMetrics
from app.rag.sqlite_retriever import SQLiteRetriever
from app.recommendation.service import RecommendationService


def test_recommendation_uses_only_seed_products(tmp_path: Path) -> None:
    db_path = tmp_path / "skin_care.db"
    init_db(db_path)
    conn = connect(db_path)
    try:
        service = RecommendationService(SQLiteRetriever(conn))
        response = service.build(
            questionnaire=Questionnaire(
                concerns=[Concern.DRYNESS, Concern.SENSITIVITY],
                budget_yen=2000,
                morning_minutes=5,
                current_items=["洗顔", "化粧水"],
            ),
            analysis=SkinAnalysis(
                source="test",
                summary="乾燥と敏感が強め",
                metrics=SkinMetrics(
                    dryness=75,
                    redness=58,
                    pores=35,
                    sebum=30,
                    dullness=40,
                    sensitivity=72,
                ),
                detected_concerns=[Concern.DRYNESS, Concern.SENSITIVITY],
            ),
            skin_log_id="test-log",
        )
    finally:
        conn.close()

    seed_ids = {
        "ceramide_lotion",
        "barrier_cream",
        "vitamin_c_serum",
        "clay_wash",
        "uv_milk",
        "balancing_gel",
    }
    assert response.buy_one.product_id in seed_ids
    assert {product.product_id for product in response.products} <= seed_ids
    assert response.skin_log_id == "test-log"

