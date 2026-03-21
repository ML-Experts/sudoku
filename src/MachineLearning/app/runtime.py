from datetime import UTC, datetime

from .schemas import RuntimeStatusResponse
from .settings import MlSettings


def build_runtime_status(settings: MlSettings) -> RuntimeStatusResponse:
    return RuntimeStatusResponse(
        status="ok",
        message=settings.ping_response_message,
        service=settings.service_name,
        version=settings.service_version,
        environment=settings.environment,
        timestamp_utc=datetime.now(UTC),
    )
