from datetime import datetime

from app.core.config import settings


def get_health_status():
    return {
        "application": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
    }