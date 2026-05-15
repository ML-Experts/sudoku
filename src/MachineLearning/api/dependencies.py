from functools import lru_cache

from fastapi import Depends, Request

from api.config.runtime_settings import (
    InferenceSettings,
    PreprocessingSettings,
    RuntimeSettings,
    TrainingSettings,
)
from application.features.datasets.commands.prepare_dataset_artifact.prepare_dataset_artifact_command_handler import (
    PrepareDatasetArtifactCommandHandler,
)
from application.features.inference.commands.infer_cell_digit.infer_cell_digit_command_handler import (
    InferCellDigitCommandHandler,
)
from application.features.preprocessing.commands.extract_cells.extract_cells_command_handler import (
    ExtractCellsCommandHandler,
)
from application.features.inference.commands.test_digit_inference.test_digit_inference_command_handler import (
    TestDigitInferenceCommandHandler,
)
from application.features.preprocessing.commands.preprocess_board.preprocess_board_command_handler import (
    PreprocessBoardCommandHandler,
)
from application.features.runtime_status.queries.get_runtime_status.get_runtime_status_query_handler import (
    GetRuntimeStatusQueryHandler,
)
from application.features.trainings.commands.cancel_training_run.cancel_training_run_command_handler import (
    CancelTrainingRunCommandHandler,
)
from application.features.trainings.commands.start_training_run.start_training_run_command_handler import (
    StartTrainingRunCommandHandler,
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
from infrastructure.datasets.board_dat_parser import BoardDatParser
from infrastructure.datasets.board_dataset_scanner import BoardDatasetScanner
from infrastructure.datasets.idx_dataset_loader import IdxDatasetLoader
from infrastructure.datasets.sample_split_assigner import SampleSplitAssigner
from infrastructure.datasets.source_resolver import DatasetSourceResolver
from infrastructure.inference.active_model_resolver import (
    FilesystemActiveModelResolver,
)
from infrastructure.inference.cell_occupancy_detector import (
    CellOccupancyDetector,
)
from infrastructure.inference.filesystem_test_image_repository import (
    FilesystemTestImageRepository,
)
from infrastructure.inference.runtime_model_loader import RuntimeModelLoader
from infrastructure.reporting.preparation_report_builder import (
    PreparationReportBuilder,
)
from infrastructure.storage.npz_dataset_artifact_writer import (
    NpzDatasetArtifactWriter,
)
from infrastructure.storage.temp_dataset_path_provider import (
    TempDatasetPathProvider,
)
from infrastructure.storage.filesystem_path_validator import (
    FilesystemPathValidator,
)
from infrastructure.text.slugify_service import PythonSlugifyService
from infrastructure.time.system_utc_clock import SystemUtcClock
from infrastructure.training.cancellation.cancellation_registry import (
    CancellationRegistry,
)
from infrastructure.training.model.model_manifest_reader import (
    ModelManifestReader,
)
from infrastructure.training.data.input_transform_factory import (
    InputTransformFactory,
)
from infrastructure.training.model.model_artifact_loader import (
    ModelArtifactLoader,
)
from infrastructure.training.model.model_factory import ModelFactory
from infrastructure.training.runners.training_runner_factory import (
    TrainingRunnerFactory,
)
from infrastructure.vision.cell_preprocessing_pipeline import (
    CellPreprocessingPipeline,
)


def get_runtime_settings(request: Request) -> RuntimeSettings:
    return request.app.state.runtime_settings


def get_preprocessing_settings(
    runtime_settings: RuntimeSettings = Depends(get_runtime_settings),
) -> PreprocessingSettings:
    return runtime_settings.preprocessing_settings


def get_training_settings(
    runtime_settings: RuntimeSettings = Depends(get_runtime_settings),
) -> TrainingSettings:
    return runtime_settings.training_settings


def get_inference_settings(
    runtime_settings: RuntimeSettings = Depends(get_runtime_settings),
) -> InferenceSettings:
    return runtime_settings.inference_settings


@lru_cache
def get_runtime_status_query_handler() -> GetRuntimeStatusQueryHandler:
    return GetRuntimeStatusQueryHandler(
        package_version_provider=ImportlibPackageVersionProvider(),
        slugify_service=PythonSlugifyService(),
        utc_clock=SystemUtcClock(),
    )


@lru_cache
def get_cancellation_registry() -> CancellationRegistry:
    return CancellationRegistry()


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


def get_start_training_run_command_handler(
    training_settings: TrainingSettings = Depends(get_training_settings),
    cancellation_registry: CancellationRegistry = Depends(
        get_cancellation_registry
    ),
) -> StartTrainingRunCommandHandler:
    utc_clock = SystemUtcClock()
    training_runner = TrainingRunnerFactory(
        settings=training_settings,
        cancellation_registry=cancellation_registry,
        utc_clock=utc_clock,
    ).create()
    return StartTrainingRunCommandHandler(
        manifest_reader=ModelManifestReader(),
        path_validator=FilesystemPathValidator(
            allowed_output_roots=training_settings.allowed_output_roots
        ),
        active_run_guard=cancellation_registry,
        training_runner=training_runner,
        utc_clock=utc_clock,
    )


def get_cancel_training_run_command_handler(
    cancellation_registry: CancellationRegistry = Depends(
        get_cancellation_registry
    ),
) -> CancelTrainingRunCommandHandler:
    return CancelTrainingRunCommandHandler(
        cancellation_registry=cancellation_registry,
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


def get_prepare_dataset_artifact_command_handler(
    runtime_settings: RuntimeSettings = Depends(get_runtime_settings),
    preprocessing_settings: PreprocessingSettings = Depends(
        get_preprocessing_settings
    ),
) -> PrepareDatasetArtifactCommandHandler:
    return PrepareDatasetArtifactCommandHandler(
        dataset_source_resolver=DatasetSourceResolver(
            boards_subdirectory=runtime_settings.boards_subdirectory,
            digits_subdirectory=runtime_settings.digits_subdirectory,
        ),
        board_dataset_scanner=BoardDatasetScanner(),
        board_dat_parser=BoardDatParser(),
        idx_dataset_loader=IdxDatasetLoader(),
        sample_split_assigner=SampleSplitAssigner(),
        cell_preprocessing_pipeline=CellPreprocessingPipeline(
            output_size=28
        ),
        npz_dataset_artifact_writer=NpzDatasetArtifactWriter(),
        temp_dataset_path_provider=TempDatasetPathProvider(
            temp_datasets_directory_path=(
                runtime_settings.temp_datasets_directory_path
            )
        ),
        preparation_report_builder=PreparationReportBuilder(),
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
    )


def get_test_digit_inference_command_handler(
    runtime_settings: RuntimeSettings = Depends(get_runtime_settings),
    training_settings: TrainingSettings = Depends(get_training_settings),
) -> TestDigitInferenceCommandHandler:
    return TestDigitInferenceCommandHandler(
        image_repository=FilesystemTestImageRepository(
            directory_path=runtime_settings.examples_uploads_directory_path
        ),
        active_model_resolver=FilesystemActiveModelResolver(
            active_model_directory_path=(
                runtime_settings.models_active_directory_path
            ),
            registry_directory_path=runtime_settings.models_registry_directory_path,
        ),
        manifest_reader=ModelManifestReader(),
        model_factory=ModelFactory(),
        artifact_loader=ModelArtifactLoader(),
        input_transform_factory=InputTransformFactory(),
        cell_preprocessing_pipeline=CellPreprocessingPipeline(output_size=28),
        device_setting=training_settings.device,
    )


def get_infer_cell_digit_command_handler(
    preprocessing_settings: PreprocessingSettings = Depends(
        get_preprocessing_settings
    ),
    inference_settings: InferenceSettings = Depends(get_inference_settings),
) -> InferCellDigitCommandHandler:
    return InferCellDigitCommandHandler(
        image_codec=OpenCvImageCodec(),
        cell_preprocessing_pipeline=CellPreprocessingPipeline(output_size=28),
        cell_occupancy_detector=CellOccupancyDetector(),
        runtime_model_loader=RuntimeModelLoader(
            manifest_reader=ModelManifestReader(),
            model_factory=ModelFactory(),
            artifact_loader=ModelArtifactLoader(),
            input_transform_factory=InputTransformFactory(),
            device_setting=inference_settings.device,
        ),
        allowed_input_mime_types=(
            preprocessing_settings.allowed_input_mime_types
        ),
        supported_input_profiles=(
            inference_settings.supported_input_profiles
        ),
    )
