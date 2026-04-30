from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from api.dependencies import get_test_digit_inference_command_handler
from api.models.error_api_response import ErrorApiResponse
from api.models.test_digit_inference_api_response import (
    TestDigitInferenceApiResponse,
)
from application.features.inference.commands.test_digit_inference.test_digit_inference_command import (
    TestDigitInferenceCommand,
)
from application.features.inference.commands.test_digit_inference.test_digit_inference_command_handler import (
    TestDigitInferenceCommandHandler,
)
from application.features.inference.errors.test_digit_inference_errors import (
    TestDigitInferenceCommandError,
)

test_inference_controller = APIRouter(prefix="/ml/test", tags=["test-inference"])


@test_inference_controller.get(
    "/inteference/{name}",
    response_model=TestDigitInferenceApiResponse,
    responses={
        404: {"model": ErrorApiResponse},
        422: {"model": ErrorApiResponse},
        500: {"model": ErrorApiResponse},
    },
)
async def test_digit_inference(
    name: str,
    command_handler: TestDigitInferenceCommandHandler = Depends(
        get_test_digit_inference_command_handler
    ),
) -> TestDigitInferenceApiResponse | JSONResponse:
    try:
        result = command_handler.handle(TestDigitInferenceCommand(image_name=name))
    except TestDigitInferenceCommandError as error:
        return _error_response(
            status_code=error.status_code,
            error_type=error.error_type,
            message=error.message,
        )
    except Exception:
        return _error_response(
            status_code=500,
            error_type="internal_server_error",
            message="Wystąpił nieobsłużony błąd testowej inferencji.",
        )

    return TestDigitInferenceApiResponse.from_dto(result)


def _error_response(
    status_code: int,
    error_type: str,
    message: str,
) -> JSONResponse:
    error_response = ErrorApiResponse(error_type=error_type, message=message)
    return JSONResponse(
        status_code=status_code,
        content=error_response.model_dump(by_alias=True),
    )
