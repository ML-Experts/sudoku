from functools import lru_cache

from fastapi import Depends, Request

from api.config.runtime_settings import (
    PreprocessingSettings,
    RuntimeSettings,
)
from application.features.preprocessing.commands.extract_cells.extract_cells_command_handler import (
    ExtractCellsCommandHandler,
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
from infrastructure.vision.opencv_board_cells_extractor import (
    OpenCvBoardCellsExtractor,
)
from infrastructure.vision.opencv_largest_contour_detector import (
    OpenCvBoardEdgeDetector,
)
from infrastructure.vision.opencv_grayscale_blur_preprocessor import (
    OpenCvGrayscaleBlurPreprocessor,
)
from infrastructure.vision.opencv_image_codec import OpenCvImageCodec
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
        board_quad_detector=OpenCvBoardEdgeDetector(
            canny_threshold_1=(
                preprocessing_settings.board_edge_canny_threshold_1
            ),
            canny_threshold_2=(
                preprocessing_settings.board_edge_canny_threshold_2
            ),
            hough_threshold=preprocessing_settings.board_edge_hough_threshold,
            min_line_length_ratio=(
                preprocessing_settings.board_edge_min_line_length_ratio
            ),
            max_line_gap_ratio=(
                preprocessing_settings.board_edge_max_line_gap_ratio
            ),
            angle_tolerance_degrees=(
                preprocessing_settings.board_edge_angle_tolerance_degrees
            ),
            outer_line_window_ratio=(
                preprocessing_settings.board_edge_outer_line_window_ratio
            ),
            minimum_board_area_ratio=(
                preprocessing_settings.board_edge_minimum_board_area_ratio
            ),
            minimum_family_segments=(
                preprocessing_settings.board_edge_minimum_family_segments
            ),
            line_position_merge_distance_ratio=(
                preprocessing_settings.board_edge_line_position_merge_distance_ratio
            ),
            minimum_distinct_lines_per_family=(
                preprocessing_settings.board_edge_minimum_distinct_lines_per_family
            ),
        ),
        perspective_transformer=OpenCvPerspectiveTransformer(
            output_board_size=preprocessing_settings.board_output_size,
            output_padding_pixels=(
                preprocessing_settings.board_output_padding_pixels
            ),
        ),
        allowed_input_mime_types=(
            preprocessing_settings.allowed_input_mime_types
        ),
        output_mime_type=preprocessing_settings.board_output_mime_type,
        board_refinement_passes=(
            preprocessing_settings.board_refinement_passes
        ),
    )


def get_extract_cells_command_handler(
    preprocessing_settings: PreprocessingSettings = Depends(
        get_preprocessing_settings
    ),
) -> ExtractCellsCommandHandler:
    return ExtractCellsCommandHandler(
        image_codec=OpenCvImageCodec(),
        board_cells_extractor=OpenCvBoardCellsExtractor(
            grid_rows=preprocessing_settings.cells_grid_rows,
            grid_cols=preprocessing_settings.cells_grid_cols,
            cell_inner_margin_ratio=(
                preprocessing_settings.cells_inner_margin_ratio
            ),
            minimum_cell_size_px=(
                preprocessing_settings.cells_minimum_cell_size_px
            ),
            output_cell_size_px=preprocessing_settings.cells_output_cell_size,
        ),
        allowed_input_mime_types=(
            preprocessing_settings.allowed_input_mime_types
        ),
        output_mime_type=preprocessing_settings.board_output_mime_type,
        expected_grid_rows=preprocessing_settings.cells_grid_rows,
        expected_grid_cols=preprocessing_settings.cells_grid_cols,
        minimum_cell_size_px=(
            preprocessing_settings.cells_minimum_cell_size_px
        ),
    )
