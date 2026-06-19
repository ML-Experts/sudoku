import logging
import sys

from fastapi import FastAPI

from api.config.environment import load_runtime_environment
from api.controllers.cell_inference_controller import (
    cell_inference_controller,
)
from api.controllers.overlay_controller import overlay_controller
from api.controllers.preprocessing_controller import (
    preprocessing_controller,
)
from api.controllers.datasets_controller import datasets_controller
from api.controllers.runtime_status_controller import (
    runtime_status_controller,
)
from api.controllers.test_inference_controller import test_inference_controller
from api.controllers.trainings_controller import trainings_controller


def _configure_logging() -> None:
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] %(message)s"
    )
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    stdout_handler = None
    for handler in root_logger.handlers:
        if isinstance(handler, logging.StreamHandler) and getattr(
            handler, "stream", None
        ) is sys.stdout:
            stdout_handler = handler
            break

    if stdout_handler is None:
        stdout_handler = logging.StreamHandler(sys.stdout)
        root_logger.addHandler(stdout_handler)

    stdout_handler.setLevel(logging.INFO)
    stdout_handler.setFormatter(formatter)


def create_app() -> FastAPI:
    _configure_logging()
    runtime_settings = load_runtime_environment()

    # Centralize app construction here so routers share one runtime configuration.
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
    app.include_router(overlay_controller)
    app.include_router(datasets_controller)
    app.include_router(trainings_controller)
    app.include_router(test_inference_controller)
    return app


app = create_app()
