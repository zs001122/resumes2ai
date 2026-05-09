from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/config")
def get_ai_config() -> dict[str, str | bool]:
    return {
        "provider": settings.ai_provider,
        "base_url": settings.ai_base_url,
        "model": settings.ai_model,
        "api_key_configured": bool(
            settings.ai_api_key and settings.ai_api_key != "YOUR_DEEPSEEK_API_KEY"
        ),
    }
