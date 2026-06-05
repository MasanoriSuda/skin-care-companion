from app.config import Settings
from app.youcam.base import YouCamAdapter
from app.youcam.mock import MockYouCamAdapter
from app.youcam.real import RealYouCamAdapter


def build_youcam_adapter(settings: Settings) -> YouCamAdapter:
    if (
        settings.youcam_mode.lower() == "real"
        and settings.youcam_api_key
        and settings.youcam_endpoint
    ):
        return RealYouCamAdapter(
            api_key=settings.youcam_api_key,
            endpoint=settings.youcam_endpoint,
            timeout_sec=settings.external_api_timeout_sec,
        )
    return MockYouCamAdapter()

