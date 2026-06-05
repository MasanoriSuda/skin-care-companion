from pathlib import Path
from typing import Protocol

from app.models import Questionnaire, SkinAnalysis


class YouCamAdapter(Protocol):
    async def analyze_image(
        self,
        image_path: Path,
        questionnaire: Questionnaire,
    ) -> SkinAnalysis:
        """Analyze an image and return a normalized skin analysis."""

