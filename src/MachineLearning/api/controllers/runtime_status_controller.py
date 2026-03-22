from fastapi import APIRouter, Depends

from MachineLearning.api.dependencies import (
    get_runtime_settings,
    get_runtime_status_query_handler,
)
from MachineLearning.api.models.runtime_status_response_model import (
    RuntimeStatusResponseModel,
)
from MachineLearning.api.config.runtime_settings import RuntimeSettings
from MachineLearning.application.features.runtime_status.queries.get_runtime_status.get_runtime_status_query import (
    GetRuntimeStatusQuery,
)
from MachineLearning.application.features.runtime_status.queries.get_runtime_status.get_runtime_status_query_handler import (
    GetRuntimeStatusQueryHandler,
)

runtime_status_controller = APIRouter(prefix="/ml", tags=["runtime"])


def _build_runtime_status_query(
    runtime_settings: RuntimeSettings,
) -> GetRuntimeStatusQuery:
    return GetRuntimeStatusQuery(
        environment=runtime_settings.environment,
        service_name=runtime_settings.service_name,
        service_version=runtime_settings.service_version,
        ping_response_message=runtime_settings.ping_response_message,
    )


@runtime_status_controller.get("/ping", response_model=str)
async def get_ping() -> str:
    return "pong"


@runtime_status_controller.get("/health", response_model=RuntimeStatusResponseModel)
async def get_health(
    runtime_settings: RuntimeSettings = Depends(get_runtime_settings),
    query_handler: GetRuntimeStatusQueryHandler = Depends(
        get_runtime_status_query_handler
    ),
) -> RuntimeStatusResponseModel:
    result = query_handler.handle(_build_runtime_status_query(runtime_settings))
    return RuntimeStatusResponseModel.from_dto(result)
