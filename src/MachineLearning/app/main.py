from fastapi import FastAPI

from .environment import get_env_value, load_runtime_environment
from .schemas import RuntimeStatusResponse

load_runtime_environment()

from .runtime import build_runtime_status


def create_app() -> FastAPI:
    app = FastAPI(
        title=get_env_value("ML_SERVICE_NAME", "sudoku-ml"),
        version=get_env_value("ML_SERVICE_VERSION", "0.1.0"),
        docs_url="/ml/docs",
        openapi_url="/ml/openapi.json",
        redoc_url="/ml/redoc",
    )

    @app.get("/ml/ping", response_model=RuntimeStatusResponse, tags=["runtime"])
    async def ping() -> RuntimeStatusResponse:
        return build_runtime_status()

    @app.get("/ml/health", response_model=RuntimeStatusResponse, tags=["runtime"])
    async def health() -> RuntimeStatusResponse:
        return build_runtime_status()

    return app


app = create_app()
