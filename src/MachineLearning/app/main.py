from typing import Annotated

from fastapi import Depends, FastAPI

from .runtime import build_runtime_status
from .schemas import RuntimeStatusResponse
from .settings import MlSettings, get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.service_name,
        version=settings.service_version,
        docs_url="/ml/docs",
        openapi_url="/ml/openapi.json",
        redoc_url="/ml/redoc",
    )

    @app.get("/ml/ping", response_model=RuntimeStatusResponse, tags=["runtime"])
    async def ping(
        ml_settings: Annotated[MlSettings, Depends(get_settings)],
    ) -> RuntimeStatusResponse:
        return build_runtime_status(ml_settings)

    @app.get("/ml/health", response_model=RuntimeStatusResponse, tags=["runtime"])
    async def health(
        ml_settings: Annotated[MlSettings, Depends(get_settings)],
    ) -> RuntimeStatusResponse:
        return build_runtime_status(ml_settings)

    return app


app = create_app()
