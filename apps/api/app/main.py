from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
import os
import shutil
import sqlite3
import tempfile
from typing import Generator

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from app.config import Settings, get_settings
from app.db.database import connect, init_db
from app.db.repository import (
    build_latest_summary,
    build_weekly_report,
    create_skin_log,
    get_skin_log,
    latest_skin_log,
    list_skin_logs,
    update_recommendations,
)
from app.models import (
    AnalyzeResponse,
    Questionnaire,
    RecommendationRequest,
    RecommendationsResponse,
    SkinLogResponse,
    WeeklyReport,
    XangiLatestSummary,
)
from app.rag import SQLiteRetriever
from app.recommendation import RecommendationService
from app.youcam import build_youcam_adapter


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    init_db(settings.database_path)
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title="Skin Care Companion API",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_conn(
    settings: Settings = Depends(get_settings),
) -> Generator[sqlite3.Connection, None, None]:
    conn = connect(settings.database_path)
    try:
        yield conn
    finally:
        conn.close()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "mode": get_settings().youcam_mode}


@app.post("/api/skin/analyze", response_model=AnalyzeResponse)
async def analyze_skin(
    questionnaire: str = Form(...),
    image: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
    conn: sqlite3.Connection = Depends(get_conn),
) -> AnalyzeResponse:
    try:
        questionnaire_obj = Questionnaire.model_validate_json(questionnaire)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc

    temp_path = _persist_upload_temporarily(image, settings.upload_dir)
    try:
        adapter = build_youcam_adapter(settings)
        analysis = await adapter.analyze_image(temp_path, questionnaire_obj)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"skin analysis failed: {exc}") from exc
    finally:
        temp_path.unlink(missing_ok=True)
        _close_upload_file(image)

    skin_log_id = create_skin_log(conn, questionnaire_obj, analysis)
    return AnalyzeResponse(
        skin_log_id=skin_log_id,
        analysis=analysis,
        image_deleted=not temp_path.exists(),
    )


@app.post("/api/recommendations", response_model=RecommendationsResponse)
def create_recommendations(
    request: RecommendationRequest,
    conn: sqlite3.Connection = Depends(get_conn),
) -> RecommendationsResponse:
    questionnaire = request.questionnaire
    analysis = request.analysis
    if request.skin_log_id and (questionnaire is None or analysis is None):
        log = get_skin_log(conn, request.skin_log_id)
        if log is None:
            raise HTTPException(status_code=404, detail="skin log not found")
        questionnaire = questionnaire or log.questionnaire
        analysis = analysis or log.analysis

    if questionnaire is None or analysis is None:
        raise HTTPException(
            status_code=400,
            detail="questionnaire and analysis are required when skin_log_id is not provided",
        )

    service = RecommendationService(SQLiteRetriever(conn))
    try:
        recommendations = service.build(
            questionnaire=questionnaire,
            analysis=analysis,
            skin_log_id=request.skin_log_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if request.skin_log_id:
        update_recommendations(conn, request.skin_log_id, recommendations)
    return recommendations


@app.get("/api/skin-logs", response_model=list[SkinLogResponse])
def get_logs(conn: sqlite3.Connection = Depends(get_conn)) -> list[SkinLogResponse]:
    return list_skin_logs(conn)


@app.get("/api/skin-logs/latest", response_model=XangiLatestSummary)
def get_latest_log_summary(
    conn: sqlite3.Connection = Depends(get_conn),
) -> XangiLatestSummary:
    return build_latest_summary(latest_skin_log(conn))


@app.get("/api/reports/weekly", response_model=WeeklyReport)
def get_weekly_report(
    conn: sqlite3.Connection = Depends(get_conn),
) -> WeeklyReport:
    return build_weekly_report(list_skin_logs(conn, limit=100), period_days=7)


def _persist_upload_temporarily(image: UploadFile, upload_dir: Path) -> Path:
    upload_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(image.filename or "face.jpg").suffix or ".jpg"
    fd, temp_name = tempfile.mkstemp(prefix="skin_", suffix=suffix, dir=upload_dir)
    with os.fdopen(fd, "wb") as buffer:
        image.file.seek(0)
        shutil.copyfileobj(image.file, buffer)
    return Path(temp_name)


def _close_upload_file(image: UploadFile) -> None:
    try:
        image.file.close()
    except Exception:
        pass
