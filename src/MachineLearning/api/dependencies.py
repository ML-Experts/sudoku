from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

from fastapi import Depends, Request

from api.config.runtime_settings import (
    InferenceSettings,
    PreprocessingSettings,
    RuntimeSettings,
    TrainingSettings,
)
from application.features.datasets.commands.create_dataset_preparation.create_dataset_preparation_command_handler import (
    CreateDatasetPreparationCommandHandler,
)
from application.features.datasets.commands.prepare_dataset_artifact.prepare_dataset_artifact_command_handler import (
    PrepareDatasetArtifactCommandHandler,
)
from application.features.overlay.commands.render_overlay_cell.render_overlay_cell_command_handler import (
    RenderOverlayCellCommandHandler,
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
from infrastructure.vision.opencv_text_overlay_renderer import (
    OpenCvTextOverlayRenderer,
)
from infrastructure.providers.package_version_provider import (
    ImportlibPackageVersionProvider,
)
from infrastructure.datasets.board_dat_parser import BoardDatParser
from infrastructure.datasets.board_dataset_scanner import BoardDatasetScanner
from infrastructure.datasets.board_folder_name_resolver import (
    BoardFolderNameResolver,
)
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
from infrastructure.reporting.preparation_report_builder import (
    PreparationReportBuilder,
)
from infrastructure.reporting.dataset_preparation_report_builder import (
    DatasetPreparationReportBuilder,
)
from infrastructure.storage.dataset_preparation_artifact_writer import (
    DatasetPreparationArtifactWriter,
)
from infrastructure.storage.npz_dataset_artifact_writer import (
    NpzDatasetArtifactWriter,
)
from infrastructure.storage.dataset_preparation_artifact_cleanup import (
    DatasetPreparationArtifactCleanup,
    DatasetPreparationWorkspaceCleanup,
)
from infrastructure.storage.dataset_preparation_manifest_writer import (
    DatasetPreparationManifestWriter,
)
from infrastructure.storage.dataset_preparation_workspace_manager import (
    DatasetPreparationWorkspaceManager,
)
from infrastructure.storage.dataset_preparations_path_provider import (
    DatasetPreparationsPathProvider,
)
from infrastructure.storage.dataset_preview_index_writer import (
    DatasetPreviewIndexWriter,
)
from infrastructure.storage.dataset_preview_path_provider import (
    DatasetPreviewPathProvider,
)
from infrastructure.storage.filesystem_image_artifact_writer import (
    FilesystemImageArtifactWriter,
)
from infrastructure.storage.json_file_writer import JsonFileWriter
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
from infrastructure.vision.cell_preprocessing_pipeline import (
    CellPreprocessingPipeline,
)
from infrastructure.vision.engine_board_dataset_cell_extractor import (
    EngineBoardDatasetCellExtractor,
)
from infrastructure.vision.engine_board_preprocessor import (
    EngineBoardPreprocessor,
)
from infrastructure.vision.engine_vision_pipeline import (
    DEFAULT_ML_READY_CELL_SIZE_PX,
    EngineVisionPipeline,
    build_engine_experiment_config_kwargs,
)
from infrastructure.vision.engine_warped_board_cells_extractor import (
    EngineWarpedBoardCellsExtractor,
)
from infrastructure.vision.vision_image_codec import VisionImageCodec

if TYPE_CHECKING:
    from application.features.inference.commands.infer_cell_digit.infer_cell_digit_command_handler import (
        InferCellDigitCommandHandler,
    )
    from application.features.inference.commands.test_digit_inference.test_digit_inference_command_handler import (
        TestDigitInferenceCommandHandler,
    )
    from application.features.trainings.commands.cancel_training_run.cancel_training_run_command_handler import (
        CancelTrainingRunCommandHandler,
    )
    from application.features.trainings.commands.start_training_run.start_training_run_command_handler import (
        StartTrainingRunCommandHandler,
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


def _build_warped_board_cells_pipeline(
    preprocessing_settings: PreprocessingSettings,
) -> EngineVisionPipeline:
    return EngineVisionPipeline(
        output_mime_type=preprocessing_settings.board_output_mime_type,
        minimum_cell_size_px=preprocessing_settings.cells_minimum_cell_size_px,
        ml_ready_cell_size_px=DEFAULT_ML_READY_CELL_SIZE_PX,
        **build_engine_experiment_config_kwargs(
            max_display_size=1600,
            adaptive_threshold_block_size=(
                preprocessing_settings.adaptive_threshold_block_size
            ),
            adaptive_threshold_c_value=preprocessing_settings.adaptive_threshold_c,
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
            warp_output_size_px=preprocessing_settings.board_output_size,
            warp_output_padding_px=(
                preprocessing_settings.board_output_padding_pixels
            ),
            warp_cell_divisions=preprocessing_settings.cells_grid_rows,
            warp_cells_output_mime_type=(
                preprocessing_settings.board_output_mime_type
            ),
            warp_cells_preview_gap_px=2,
        ),
    )


def get_preprocess_board_command_handler(
    preprocessing_settings: PreprocessingSettings = Depends(
        get_preprocessing_settings
    ),
) -> PreprocessBoardCommandHandler:
    board_pipeline = _build_warped_board_cells_pipeline(preprocessing_settings)
    return PreprocessBoardCommandHandler(
        image_codec=VisionImageCodec(),
        board_preprocessor=EngineBoardPreprocessor(board_pipeline),
        allowed_input_mime_types=(
            preprocessing_settings.allowed_input_mime_types
        ),
        output_mime_type=preprocessing_settings.board_output_mime_type,
    )


def get_start_training_run_command_handler(
    training_settings: TrainingSettings = Depends(get_training_settings),
    cancellation_registry: CancellationRegistry = Depends(
        get_cancellation_registry
    ),
) -> StartTrainingRunCommandHandler:
    from application.features.trainings.commands.start_training_run.start_training_run_command_handler import (
        StartTrainingRunCommandHandler,
    )
    from infrastructure.training.runners.training_runner_factory import (
        TrainingRunnerFactory,
    )

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
    from application.features.trainings.commands.cancel_training_run.cancel_training_run_command_handler import (
        CancelTrainingRunCommandHandler,
    )

    return CancelTrainingRunCommandHandler(
        cancellation_registry=cancellation_registry,
    )


def get_extract_cells_command_handler(
    preprocessing_settings: PreprocessingSettings = Depends(
        get_preprocessing_settings
    ),
) -> ExtractCellsCommandHandler:
    cells_pipeline = _build_warped_board_cells_pipeline(preprocessing_settings)
    return ExtractCellsCommandHandler(
        image_codec=VisionImageCodec(),
        board_cells_extractor=EngineWarpedBoardCellsExtractor(
            pipeline=cells_pipeline,
            grid_rows=preprocessing_settings.cells_grid_rows,
            grid_cols=preprocessing_settings.cells_grid_cols,
        ),
        allowed_input_mime_types=(
            preprocessing_settings.allowed_input_mime_types
        ),
        output_mime_type=preprocessing_settings.board_output_mime_type,
        expected_grid_rows=preprocessing_settings.cells_grid_rows,
        expected_grid_cols=preprocessing_settings.cells_grid_cols,
    )


def get_render_overlay_cell_command_handler(
    preprocessing_settings: PreprocessingSettings = Depends(
        get_preprocessing_settings
    ),
) -> RenderOverlayCellCommandHandler:
    return RenderOverlayCellCommandHandler(
        image_codec=VisionImageCodec(),
        text_overlay_renderer=OpenCvTextOverlayRenderer(),
        allowed_input_mime_types=(
            preprocessing_settings.allowed_input_mime_types
        ),
    )


def get_prepare_dataset_artifact_command_handler(
    runtime_settings: RuntimeSettings = Depends(get_runtime_settings),
    preprocessing_settings: PreprocessingSettings = Depends(
        get_preprocessing_settings
    ),
) -> PrepareDatasetArtifactCommandHandler:
    cells_pipeline = _build_warped_board_cells_pipeline(
        preprocessing_settings
    )
    dataset_preview_path_provider = DatasetPreviewPathProvider(
        previews_directory_path=runtime_settings.dataset_previews_directory_path
    )
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
            output_size=28,
            adaptive_block_size=preprocessing_settings.adaptive_threshold_block_size,
            adaptive_c=preprocessing_settings.adaptive_threshold_c,
        ),
        npz_dataset_artifact_writer=NpzDatasetArtifactWriter(),
        temp_dataset_path_provider=TempDatasetPathProvider(
            temp_datasets_directory_path=(
                runtime_settings.temp_datasets_directory_path
            )
        ),
        dataset_preview_path_provider=dataset_preview_path_provider,
        preview_image_artifact_writer=FilesystemImageArtifactWriter(
            image_codec=VisionImageCodec(),
            output_mime_type="image/png",
        ),
        dataset_preview_index_writer=DatasetPreviewIndexWriter(
            json_file_writer=JsonFileWriter()
        ),
        dataset_preparation_artifact_cleanup=DatasetPreparationArtifactCleanup(
            dataset_preview_path_provider=dataset_preview_path_provider
        ),
        preparation_report_builder=PreparationReportBuilder(),
        board_dataset_cell_extractor=EngineBoardDatasetCellExtractor(
            pipeline=cells_pipeline,
        ),
    )


def get_create_dataset_preparation_command_handler(
    runtime_settings: RuntimeSettings = Depends(get_runtime_settings),
    preprocessing_settings: PreprocessingSettings = Depends(
        get_preprocessing_settings
    ),
) -> CreateDatasetPreparationCommandHandler:
    cells_pipeline = _build_warped_board_cells_pipeline(
        preprocessing_settings
    )
    path_provider = DatasetPreparationsPathProvider(
        runtime_settings.dataset_preparations_directory_path
    )
    workspace_manager = DatasetPreparationWorkspaceManager(path_provider)
    return CreateDatasetPreparationCommandHandler(
        dataset_source_resolver=DatasetSourceResolver(
            boards_subdirectory=runtime_settings.boards_subdirectory,
            digits_subdirectory=runtime_settings.digits_subdirectory,
        ),
        board_dataset_scanner=BoardDatasetScanner(),
        board_dat_parser=BoardDatParser(),
        idx_dataset_loader=IdxDatasetLoader(),
        board_dataset_cell_extractor=EngineBoardDatasetCellExtractor(
            pipeline=cells_pipeline,
        ),
        cell_preprocessing_pipeline=CellPreprocessingPipeline(
            output_size=28,
            adaptive_block_size=preprocessing_settings.adaptive_threshold_block_size,
            adaptive_c=preprocessing_settings.adaptive_threshold_c,
        ),
        artifact_writer=DatasetPreparationArtifactWriter(
            path_provider=path_provider,
            image_artifact_writer=FilesystemImageArtifactWriter(
                image_codec=VisionImageCodec(),
                output_mime_type="image/png",
            ),
        ),
        manifest_writer=DatasetPreparationManifestWriter(
            path_provider=path_provider,
            json_file_writer=JsonFileWriter(),
        ),
        workspace_manager=workspace_manager,
        artifact_cleanup=DatasetPreparationWorkspaceCleanup(
            workspace_manager=workspace_manager
        ),
        board_folder_name_resolver=BoardFolderNameResolver(),
        report_builder=DatasetPreparationReportBuilder(),
        utc_clock=SystemUtcClock(),
    )


def get_test_digit_inference_command_handler(
    runtime_settings: RuntimeSettings = Depends(get_runtime_settings),
    training_settings: TrainingSettings = Depends(get_training_settings),
    preprocessing_settings: PreprocessingSettings = Depends(
        get_preprocessing_settings
    ),
) -> TestDigitInferenceCommandHandler:
    from application.features.inference.commands.test_digit_inference.test_digit_inference_command_handler import (
        TestDigitInferenceCommandHandler,
    )
    from infrastructure.inference.runtime_model_loader import RuntimeModelLoader
    from infrastructure.training.data.input_transform_factory import (
        InputTransformFactory,
    )
    from infrastructure.training.model.model_artifact_loader import (
        ModelArtifactLoader,
    )
    from infrastructure.training.model.model_factory import ModelFactory

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
        cell_preprocessing_pipeline=CellPreprocessingPipeline(
            output_size=28,
            adaptive_block_size=preprocessing_settings.adaptive_threshold_block_size,
            adaptive_c=preprocessing_settings.adaptive_threshold_c,
        ),
        device_setting=training_settings.device,
    )


def get_infer_cell_digit_command_handler(
    preprocessing_settings: PreprocessingSettings = Depends(
        get_preprocessing_settings
    ),
    inference_settings: InferenceSettings = Depends(get_inference_settings),
) -> InferCellDigitCommandHandler:
    from application.features.inference.commands.infer_cell_digit.infer_cell_digit_command_handler import (
        InferCellDigitCommandHandler,
    )
    from infrastructure.inference.runtime_model_loader import RuntimeModelLoader
    from infrastructure.training.data.input_transform_factory import (
        InputTransformFactory,
    )
    from infrastructure.training.model.model_artifact_loader import (
        ModelArtifactLoader,
    )
    from infrastructure.training.model.model_factory import ModelFactory

    return InferCellDigitCommandHandler(
        image_codec=VisionImageCodec(),
        cell_preprocessing_pipeline=CellPreprocessingPipeline(
            output_size=28,
            adaptive_block_size=preprocessing_settings.adaptive_threshold_block_size,
            adaptive_c=preprocessing_settings.adaptive_threshold_c,
        ),
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
