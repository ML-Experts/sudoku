from fastapi import FastAPI

from api.config.environment import load_runtime_environment
from api.controllers.cell_inference_controller import (
    cell_inference_controller,
)
from api.controllers.preprocessing_controller import (
    preprocessing_controller,
)
from api.controllers.datasets_controller import datasets_controller
from api.controllers.runtime_status_controller import (
    runtime_status_controller,
)
from api.controllers.test_inference_controller import test_inference_controller
from api.controllers.trainings_controller import trainings_controller


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
    app.include_router(preprocessing_controller)
    app.include_router(cell_inference_controller)
    app.include_router(datasets_controller)
    app.include_router(trainings_controller)
    app.include_router(test_inference_controller)
    return app


app = create_app()
