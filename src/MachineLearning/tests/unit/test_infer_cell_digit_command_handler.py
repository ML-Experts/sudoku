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

    def build_foreground_mask(self, cell_image: np.ndarray) -> np.ndarray:
        if self._should_fail:
            raise ValueError("cannot preprocess")
        return np.ones((28, 28), dtype=np.uint8) * 255

    def run(self, cell_image: np.ndarray) -> np.ndarray:
        if self._should_fail:
            raise ValueError("cannot preprocess")
        return np.ones((28, 28), dtype=np.float32)


class _CellOccupancyDetector:
    def __init__(self, is_empty: bool) -> None:
        self._is_empty = is_empty
        self.last_kwargs: dict[str, float] | None = None

    def detect(
        self,
        image: np.ndarray,
        inner_margin_ratio: float,
        dark_pixel_ratio_threshold: float,
        center_area_ratio: float,
        min_component_area_ratio: float,
        line_artifact_min_span_ratio: float,
        line_artifact_max_thickness_ratio: float,
    ) -> CellOccupancy:
        self.last_kwargs = {
            "inner_margin_ratio": inner_margin_ratio,
            "dark_pixel_ratio_threshold": dark_pixel_ratio_threshold,
            "center_area_ratio": center_area_ratio,
            "min_component_area_ratio": min_component_area_ratio,
            "line_artifact_min_span_ratio": line_artifact_min_span_ratio,
            "line_artifact_max_thickness_ratio": line_artifact_max_thickness_ratio,
        }
        return CellOccupancy(
            is_empty=self._is_empty,
            dark_pixel_ratio=0.0 if self._is_empty else 0.1,
        )


class _RuntimeModelLoader:
    def __init__(self, predicted_digit: int) -> None:
        self.predicted_digit = predicted_digit
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
            model=_PredictingModel(self.predicted_digit),
            input_transform=lambda image: torch.as_tensor(image, dtype=torch.float32),
            device=torch.device("cpu"),
        )


class _PredictingModel(torch.nn.Module):
    def __init__(self, predicted_digit: int) -> None:
        super().__init__()
        self._predicted_digit = predicted_digit

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        output = torch.zeros((x.shape[0], 10), dtype=torch.float32)
        output[:, self._predicted_digit] = 1.0
        return output


class InferCellDigitCommandHandlerTests(unittest.TestCase):
    def test_handle_should_return_digit_when_cell_is_not_empty(self) -> None:
        runtime_model_loader = _RuntimeModelLoader(predicted_digit=7)
        occupancy_detector = _CellOccupancyDetector(is_empty=False)
        handler = self._create_handler(
            occupancy_detector=occupancy_detector,
            runtime_model_loader=runtime_model_loader,
        )

        result = handler.handle(self._command())

        self.assertEqual(result.digit, 7)
        self.assertTrue(runtime_model_loader.was_called)
        self.assertEqual(
            occupancy_detector.last_kwargs,
            {
                "inner_margin_ratio": 0.12,
                "dark_pixel_ratio_threshold": 0.02,
                "center_area_ratio": 0.5,
                "min_component_area_ratio": 0.02,
                "line_artifact_min_span_ratio": 0.5,
                "line_artifact_max_thickness_ratio": 0.07,
            },
        )

    def test_handle_should_return_null_without_loading_model_for_empty_cell(
        self,
    ) -> None:
        runtime_model_loader = _RuntimeModelLoader(predicted_digit=7)
        handler = self._create_handler(
            occupancy_detector=_CellOccupancyDetector(is_empty=True),
            runtime_model_loader=runtime_model_loader,
        )

        result = handler.handle(self._command())

        self.assertIsNone(result.digit)
        self.assertFalse(runtime_model_loader.was_called)

    def test_handle_should_reject_input_profile_mismatch(self) -> None:
        handler = self._create_handler(
            occupancy_detector=_CellOccupancyDetector(is_empty=False),
            runtime_model_loader=_RuntimeModelLoader(predicted_digit=7),
        )
        command = self._command(input_profile="other-profile")

        with self.assertRaises(CellDigitInferenceValidationError) as context:
            handler.handle(command)

        self.assertEqual(context.exception.error_type, "input_profile_mismatch")

    def test_handle_should_map_preprocessing_failure_to_422(self) -> None:
        handler = self._create_handler(
            occupancy_detector=_CellOccupancyDetector(is_empty=False),
            runtime_model_loader=_RuntimeModelLoader(predicted_digit=7),
            preprocessing_pipeline=_CellPreprocessingPipeline(should_fail=True),
        )

        with self.assertRaises(CellDigitInferenceValidationError) as context:
            handler.handle(self._command())

        self.assertEqual(
            context.exception.error_type,
            "cell_image_not_processable",
        )

    def test_handle_should_reject_digit_zero_from_model(self) -> None:
        handler = self._create_handler(
            occupancy_detector=_CellOccupancyDetector(is_empty=False),
            runtime_model_loader=_RuntimeModelLoader(predicted_digit=0),
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
                empty_cell_inner_margin_ratio=0.12,
                empty_cell_dark_pixel_ratio_threshold=0.02,
                center_area_ratio=0.5,
                min_component_area_ratio=0.02,
                line_artifact_min_span_ratio=0.5,
                line_artifact_max_thickness_ratio=0.07,
            ),
        )


if __name__ == "__main__":
    unittest.main()
