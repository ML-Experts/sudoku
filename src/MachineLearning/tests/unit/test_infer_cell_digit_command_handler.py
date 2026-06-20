import unittest
from types import SimpleNamespace

import numpy as np
import torch

from application.features.inference.commands.infer_cell_digit.infer_cell_digit_command import (
    InferCellDigitCommand,
)
from application.features.inference.commands.infer_cell_digit.infer_cell_digit_command_handler import (
    InferCellDigitCommandHandler,
)
from application.features.inference.dto.inference_runtime_configuration_dto import (
    InferenceRuntimeConfigurationDto,
)
from application.features.inference.dto.inference_runtime_model_reference_dto import (
    InferenceRuntimeModelReferenceDto,
)
from application.features.inference.errors.cell_digit_inference_errors import (
    CellDigitInferenceValidationError,
)
from models.cell_occupancy import CellOccupancy


class _ImageCodec:
    def decode_base64_image(
        self,
        base64_image: str,
        mime_type: str,
    ) -> object:
        return object()

    def decode_image(self, image: object) -> np.ndarray:
        return np.zeros((32, 32, 3), dtype=np.uint8)


class _CellPreprocessingPipeline:
    def __init__(self, should_fail: bool = False) -> None:
        self._should_fail = should_fail
        self.run_calls = 0

    def run(self, cell_image: np.ndarray) -> np.ndarray:
        self.run_calls += 1
        if self._should_fail:
            raise ValueError("cannot preprocess")
        return np.ones((28, 28), dtype=np.float32)


class _CellOccupancyDetector:
    def __init__(self, is_empty: bool) -> None:
        self._is_empty = is_empty
        self.last_kwargs: dict[str, float | int] | None = None
        self.last_image_shape: tuple[int, ...] | None = None

    def detect(
        self,
        image: np.ndarray,
        inner_margin_ratio: float,
        dark_pixel_ratio_threshold: float,
        center_area_ratio: float,
        min_component_area_ratio: float,
        line_artifact_min_span_ratio: float,
        line_artifact_max_thickness_ratio: float,
        empty_cell_min_segment_length_px: int,
        empty_cell_filtered_segment_count_threshold: int,
    ) -> CellOccupancy:
        self.last_image_shape = image.shape
        self.last_kwargs = {
            "inner_margin_ratio": inner_margin_ratio,
            "dark_pixel_ratio_threshold": dark_pixel_ratio_threshold,
            "center_area_ratio": center_area_ratio,
            "min_component_area_ratio": min_component_area_ratio,
            "line_artifact_min_span_ratio": line_artifact_min_span_ratio,
            "line_artifact_max_thickness_ratio": line_artifact_max_thickness_ratio,
            "empty_cell_min_segment_length_px": empty_cell_min_segment_length_px,
            "empty_cell_filtered_segment_count_threshold": (
                empty_cell_filtered_segment_count_threshold
            ),
        }
        return CellOccupancy(
            is_empty=self._is_empty,
            foreground_pixel_count=0 if self._is_empty else 24,
            foreground_pixel_ratio=0.0 if self._is_empty else 0.1,
            filtered_segment_count=0 if self._is_empty else 2,
            accept_by_pixels=not self._is_empty,
            accept_by_segments=not self._is_empty,
        )


class _RuntimeModelLoader:
    def __init__(
        self,
        predicted_class_index: int,
        output_classes: int = 9,
    ) -> None:
        self.predicted_class_index = predicted_class_index
        self.output_classes = output_classes
        self.was_called = False

    def load(
        self,
        manifest_path: str,
        artifact_path: str,
        input_profile: str,
        inference_profile_name: str,
    ) -> object:
        self.was_called = True
        return SimpleNamespace(
            model=_PredictingModel(
                self.predicted_class_index,
                output_classes=self.output_classes,
            ),
            input_transform=lambda image: torch.as_tensor(image, dtype=torch.float32),
            device=torch.device("cpu"),
        )


class _PredictingModel(torch.nn.Module):
    def __init__(
        self,
        predicted_class_index: int,
        output_classes: int = 9,
    ) -> None:
        super().__init__()
        self._predicted_class_index = predicted_class_index
        self._output_classes = output_classes

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        output = torch.zeros((x.shape[0], self._output_classes), dtype=torch.float32)
        output[:, self._predicted_class_index] = 1.0
        return output


class InferCellDigitCommandHandlerTests(unittest.TestCase):
    def test_handle_should_return_digit_when_cell_is_not_empty(self) -> None:
        runtime_model_loader = _RuntimeModelLoader(predicted_class_index=6)
        occupancy_detector = _CellOccupancyDetector(is_empty=False)
        preprocessing_pipeline = _CellPreprocessingPipeline()
        handler = self._create_handler(
            occupancy_detector=occupancy_detector,
            runtime_model_loader=runtime_model_loader,
            preprocessing_pipeline=preprocessing_pipeline,
        )

        result = handler.handle(self._command())

        self.assertEqual(result.digit, 7)
        self.assertTrue(runtime_model_loader.was_called)
        self.assertEqual(preprocessing_pipeline.run_calls, 1)
        self.assertEqual(occupancy_detector.last_image_shape, (32, 32, 3))
        self.assertEqual(
            occupancy_detector.last_kwargs,
            {
                "inner_margin_ratio": 0.0,
                "dark_pixel_ratio_threshold": 0.15,
                "center_area_ratio": 0.5,
                "min_component_area_ratio": 0.00008,
                "line_artifact_min_span_ratio": 0.5,
                "line_artifact_max_thickness_ratio": 0.07,
                "empty_cell_min_segment_length_px": 15,
                "empty_cell_filtered_segment_count_threshold": 5,
            },
        )

    def test_handle_should_return_null_without_loading_model_for_empty_cell(
        self,
    ) -> None:
        runtime_model_loader = _RuntimeModelLoader(predicted_class_index=6)
        preprocessing_pipeline = _CellPreprocessingPipeline()
        handler = self._create_handler(
            occupancy_detector=_CellOccupancyDetector(is_empty=True),
            runtime_model_loader=runtime_model_loader,
            preprocessing_pipeline=preprocessing_pipeline,
        )

        result = handler.handle(self._command())

        self.assertIsNone(result.digit)
        self.assertFalse(runtime_model_loader.was_called)
        self.assertEqual(preprocessing_pipeline.run_calls, 0)

    def test_handle_should_reject_input_profile_mismatch(self) -> None:
        handler = self._create_handler(
            occupancy_detector=_CellOccupancyDetector(is_empty=False),
            runtime_model_loader=_RuntimeModelLoader(predicted_class_index=6),
        )
        command = self._command(input_profile="other-profile")

        with self.assertRaises(CellDigitInferenceValidationError) as context:
            handler.handle(command)

        self.assertEqual(context.exception.error_type, "input_profile_mismatch")

    def test_handle_should_map_preprocessing_failure_to_422(self) -> None:
        handler = self._create_handler(
            occupancy_detector=_CellOccupancyDetector(is_empty=False),
            runtime_model_loader=_RuntimeModelLoader(predicted_class_index=6),
            preprocessing_pipeline=_CellPreprocessingPipeline(should_fail=True),
        )

        with self.assertRaises(CellDigitInferenceValidationError) as context:
            handler.handle(self._command())

        self.assertEqual(
            context.exception.error_type,
            "cell_image_not_processable",
        )

    def test_handle_should_map_first_sudoku_class_to_digit_one(self) -> None:
        handler = self._create_handler(
            occupancy_detector=_CellOccupancyDetector(is_empty=False),
            runtime_model_loader=_RuntimeModelLoader(predicted_class_index=0),
        )

        result = handler.handle(self._command())

        self.assertEqual(result.digit, 1)

    def test_handle_should_reject_out_of_contract_class_index(self) -> None:
        handler = self._create_handler(
            occupancy_detector=_CellOccupancyDetector(is_empty=False),
            runtime_model_loader=_RuntimeModelLoader(
                predicted_class_index=9,
                output_classes=10,
            ),
        )

        with self.assertRaises(CellDigitInferenceValidationError) as context:
            handler.handle(self._command())

        self.assertEqual(context.exception.error_type, "invalid_inference_result")

    def _create_handler(
        self,
        occupancy_detector: _CellOccupancyDetector,
        runtime_model_loader: _RuntimeModelLoader,
        preprocessing_pipeline: _CellPreprocessingPipeline | None = None,
    ) -> InferCellDigitCommandHandler:
        return InferCellDigitCommandHandler(
            image_codec=_ImageCodec(),
            cell_preprocessing_pipeline=(
                preprocessing_pipeline or _CellPreprocessingPipeline()
            ),
            cell_occupancy_detector=occupancy_detector,
            runtime_model_loader=runtime_model_loader,
            allowed_input_mime_types=("image/png",),
            supported_input_profiles=("default-28x28-v1",),
        )

    def _command(
        self,
        input_profile: str = "default-28x28-v1",
    ) -> InferCellDigitCommand:
        return InferCellDigitCommand(
            mime_type="image/png",
            base64_image="dGVzdA==",
            active_model=InferenceRuntimeModelReferenceDto(
                name="digit-model",
                manifest_path="/tmp/model.json",
                primary_artifact_path="/tmp/model.pt",
                input_profile=input_profile,
            ),
            resolved_configuration=InferenceRuntimeConfigurationDto(
                inference_profile_name="default-28x28-v1",
                empty_cell_inner_margin_ratio=0.0,
                empty_cell_dark_pixel_ratio_threshold=0.15,
                center_area_ratio=0.5,
                min_component_area_ratio=0.00008,
                line_artifact_min_span_ratio=0.5,
                line_artifact_max_thickness_ratio=0.07,
                empty_cell_min_segment_length_px=15,
                empty_cell_filtered_segment_count_threshold=5,
            ),
        )


if __name__ == "__main__":
    unittest.main()
