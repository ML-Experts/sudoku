from functools import lru_cache

from fastapi import Depends, Request

from api.config.runtime_settings import (
    PreprocessingSettings,
    RuntimeSettings,
)
from application.features.preprocessing.commands.preprocess_board.preprocess_board_command_handler import (
    PreprocessBoardCommandHandler,
)
from application.features.runtime_status.queries.get_runtime_status.get_runtime_status_query_handler import (
    GetRuntimeStatusQueryHandler,
)
from infrastructure.vision.opencv_adaptive_threshold_binarizer import (
    OpenCvAdaptiveThresholdBinarizer,
)
from infrastructure.vision.opencv_grayscale_blur_preprocessor import (
    OpenCvGrayscaleBlurPreprocessor,
)
from infrastructure.vision.opencv_image_codec import OpenCvImageCodec
from infrastructure.vision.opencv_largest_contour_detector import (
    OpenCvLargestContourDetector,
)
from infrastructure.vision.opencv_perspective_transformer import (
    OpenCvPerspectiveTransformer,
)
from infrastructure.providers.package_version_provider import (
    ImportlibPackageVersionProvider,
)
from infrastructure.text.slugify_service import PythonSlugifyService
from infrastructure.time.system_utc_clock import SystemUtcClock


def get_runtime_settings(request: Request) -> RuntimeSettings:
    return request.app.state.runtime_settings


def get_preprocessing_settings(
    runtime_settings: RuntimeSettings = Depends(get_runtime_settings),
) -> PreprocessingSettings:
    return runtime_settings.preprocessing_settings


@lru_cache
def get_runtime_status_query_handler() -> GetRuntimeStatusQueryHandler:
    return GetRuntimeStatusQueryHandler(
        package_version_provider=ImportlibPackageVersionProvider(),
        slugify_service=PythonSlugifyService(),
        utc_clock=SystemUtcClock(),
    )


def get_preprocess_board_command_handler(
    preprocessing_settings: PreprocessingSettings = Depends(
        get_preprocessing_settings
    ),
) -> PreprocessBoardCommandHandler:
    return PreprocessBoardCommandHandler(
        image_codec=OpenCvImageCodec(),
        grayscale_blur_preprocessor=OpenCvGrayscaleBlurPreprocessor(
            grayscale_color_conversion_code=(
                preprocessing_settings.grayscale_color_conversion_code
            ),
            gaussian_kernel_size=preprocessing_settings.gaussian_kernel_size,
            gaussian_sigma_x=preprocessing_settings.gaussian_sigma_x,
        ),
        adaptive_threshold_binarizer=OpenCvAdaptiveThresholdBinarizer(
            block_size=preprocessing_settings.adaptive_threshold_block_size,
            c_value=preprocessing_settings.adaptive_threshold_c,
        ),
        largest_contour_detector=OpenCvLargestContourDetector(
            contour_retrieval_mode=(
                preprocessing_settings.contour_retrieval_mode
            ),
            contour_approximation_mode=(
                preprocessing_settings.contour_approximation_mode
            ),
            polygon_epsilon_factor=(
                preprocessing_settings.polygon_epsilon_factor
            ),
        ),
        perspective_transformer=OpenCvPerspectiveTransformer(
            output_board_size=preprocessing_settings.board_output_size
        ),
        allowed_input_mime_types=(
            preprocessing_settings.allowed_input_mime_types
        ),
        output_mime_type=preprocessing_settings.board_output_mime_type,
    )
