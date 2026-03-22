from fastapi import FastAPI

from MachineLearning.api.config.environment import load_runtime_environment
from MachineLearning.api.controllers.runtime_status_controller import (
    runtime_status_controller,
)


def create_app() -> FastAPI:
    runtime_settings = load_runtime_environment()

    app = FastAPI(
        title=runtime_settings.service_name,
        version=runtime_settings.service_version,
        docs_url="/ml/docs",
        openapi_url="/ml/openapi.json",
        redoc_url="/ml/redoc",
    )
    app.state.runtime_settings = runtime_settings
    app.include_router(runtime_status_controller)
    return app


app = create_app()
