import json
import tempfile
import unittest
from pathlib import Path

import torch

from application.features.inference.errors.cell_digit_inference_errors import (
    CellDigitInferenceValidationError,
)
from infrastructure.inference.runtime_model_loader import RuntimeModelLoader
from infrastructure.training.data.input_transform_factory import (
    InputTransformFactory,
)
from infrastructure.training.model.custom_digit_cnn_v1 import CustomDigitCnnV1
from infrastructure.training.model.model_artifact_loader import (
    ModelArtifactLoader,
)
from infrastructure.training.model.model_factory import ModelFactory
from infrastructure.training.model.model_manifest_reader import (
    ModelManifestReader,
)


class RuntimeModelLoaderTests(unittest.TestCase):
    def test_load_should_prepare_runtime_model_for_inference(self) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            model_directory = Path(temp_directory) / "model"
            manifest_path, artifact_path = self._write_model(
                model_directory,
                can_use_for_inference=True,
                num_classes=9,
            )
            loader = self._create_loader()

            runtime_model = loader.load(
                manifest_path=str(manifest_path),
                artifact_path=str(artifact_path),
                input_profile="default-28x28-v1",
                inference_profile_name="default-28x28-v1",
            )

            self.assertEqual(runtime_model.device.type, "cpu")
            self.assertEqual(
                runtime_model.manifest.architecture.input_profile,
                "default-28x28-v1",
            )

    def test_load_should_reject_model_without_inference_capability(self) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            model_directory = Path(temp_directory) / "model"
            manifest_path, artifact_path = self._write_model(
                model_directory,
                can_use_for_inference=False,
                num_classes=9,
            )
            loader = self._create_loader()

            with self.assertRaises(CellDigitInferenceValidationError) as context:
                loader.load(
                    manifest_path=str(manifest_path),
                    artifact_path=str(artifact_path),
                    input_profile="default-28x28-v1",
                    inference_profile_name="default-28x28-v1",
                )

        self.assertEqual(context.exception.error_type, "inference_model_not_allowed")

    def test_load_should_reject_model_with_non_sudoku_digit_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            model_directory = Path(temp_directory) / "model"
            manifest_path, artifact_path = self._write_model(
                model_directory,
                can_use_for_inference=True,
                num_classes=10,
            )
            loader = self._create_loader()

            with self.assertRaises(CellDigitInferenceValidationError) as context:
                loader.load(
                    manifest_path=str(manifest_path),
                    artifact_path=str(artifact_path),
                    input_profile="default-28x28-v1",
                    inference_profile_name="default-28x28-v1",
                )

        self.assertEqual(context.exception.error_type, "inference_model_not_allowed")

    def test_load_should_fail_when_artifact_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            model_directory = Path(temp_directory) / "model"
            manifest_path, artifact_path = self._write_model(
                model_directory,
                can_use_for_inference=True,
                num_classes=9,
            )
            artifact_path.unlink()
            loader = self._create_loader()

            with self.assertRaises(CellDigitInferenceValidationError) as context:
                loader.load(
                    manifest_path=str(manifest_path),
                    artifact_path=str(artifact_path),
                    input_profile="default-28x28-v1",
                    inference_profile_name="default-28x28-v1",
                )

        self.assertEqual(context.exception.error_type, "model_artifact_not_found")

    def _create_loader(self) -> RuntimeModelLoader:
        return RuntimeModelLoader(
            manifest_reader=ModelManifestReader(),
            model_factory=ModelFactory(),
            artifact_loader=ModelArtifactLoader(),
            input_transform_factory=InputTransformFactory(),
            device_setting="cpu",
        )

    def _write_model(
        self,
        model_directory: Path,
        can_use_for_inference: bool,
        num_classes: int,
    ) -> tuple[Path, Path]:
        artifacts_directory = model_directory / "artifacts"
        artifacts_directory.mkdir(parents=True)
        manifest_path = model_directory / "model.json"
        artifact_path = artifacts_directory / "model.pt"

        model = CustomDigitCnnV1(num_classes=num_classes)
        torch.save(model.state_dict(), artifact_path)
        manifest_path.write_text(
            json.dumps(
                {
                    "framework": "pytorch",
                    "architecture": {
                        "type": "custom-cnn-v1",
                        "family": "cnn",
                        "numClasses": num_classes,
                        "inputChannels": 1,
                        "inputHeight": 28,
                        "inputWidth": 28,
                        "inputProfile": "default-28x28-v1",
                    },
                    "artifacts": {
                        "primaryArtifactRelativePath": "artifacts/model.pt",
                        "format": "pytorch-state-dict",
                    },
                    "capabilities": {
                        "canStartTraining": True,
                        "canUseForInference": can_use_for_inference,
                    },
                }
            ),
            encoding="utf-8",
        )
        return manifest_path, artifact_path


if __name__ == "__main__":
    unittest.main()
