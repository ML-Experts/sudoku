import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from application.features.trainings.dto.training_run_context_dto import (
    BaseModelReferenceDto,
    OutputRegistryModelDto,
    ProcessedDatasetReferenceDto,
    ResolvedTrainingConfigurationDto,
    TrainingParametersDto,
    TrainingOutputPathsDto,
    TrainingRunContextDto,
)
from infrastructure.training.cancellation.cancellation_registry import (
    CancellationRegistry,
)
from infrastructure.training.cancellation.cancellation_token import CancellationToken
from infrastructure.training.profiles.training_profile import TrainingProfile
from infrastructure.training.runners.pytorch_training_runner import (
    BEST_CHECKPOINT_FILE_NAME,
    PytorchTrainingRunner,
)
from models.model_manifest import (
    ModelArchitecture,
    ModelArtifacts,
    ModelCapabilities,
    ModelManifest,
)


class _Publisher:
    def __init__(self) -> None:
        self.events = []

    async def publish(self, event, *, terminal: bool = False) -> None:
        self.events.append((event, terminal))


class _Clock:
    def now(self) -> datetime:
        return datetime(2026, 5, 13, 3, 30, tzinfo=UTC)


class _ProfileCatalog:
    def create_effective_profile(
        self,
        manifest: ModelManifest,
        training_parameters: TrainingParametersDto,
        profile_name: str | None = None,
    ) -> TrainingProfile:
        return TrainingProfile(
            name=profile_name or "runtime",
            architecture_family=manifest.architecture.family,
            epochs=training_parameters.epochs,
            batch_size=training_parameters.batch_size,
            learning_rate=training_parameters.learning_rate,
            optimizer="adam",
            fine_tuning_policy=training_parameters.fine_tuning_policy,
            early_stopping_patience=training_parameters.early_stopping_patience,
            early_stopping_min_delta=training_parameters.early_stopping_min_delta,
            warmup_epochs=training_parameters.warmup_epochs,
            lr_scheduler_patience=training_parameters.lr_scheduler_patience,
            lr_scheduler_factor=training_parameters.lr_scheduler_factor,
        )


class _MarkerModel(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.weight = nn.Parameter(torch.tensor([0.0], dtype=torch.float32))
        self.register_buffer(
            "epoch_marker",
            torch.tensor([0.0], dtype=torch.float32),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        batch_size = x.shape[0]
        return torch.zeros((batch_size, 1), dtype=torch.float32, device=x.device)


class _ModelFactory:
    def build(self, manifest: ModelManifest) -> nn.Module:
        return _MarkerModel()


class _ArtifactLoader:
    def load(
        self,
        model: nn.Module,
        artifact_path: str,
        manifest: ModelManifest,
        device: torch.device,
    ) -> None:
        return None


class _InputTransformFactory:
    def build(
        self,
        manifest: ModelManifest,
        augmentation_profile_name: str,
    ):
        return lambda image: torch.as_tensor(image, dtype=torch.float32)


class _Arrays:
    def __init__(self) -> None:
        self.class_names = ("0",)


class _DatasetLoader:
    def load(self, dataset_path: str) -> _Arrays:
        return _Arrays()


class _DataloaderFactory:
    def build(self, arrays, transform, batch_size: int) -> dict[str, DataLoader]:
        images = torch.zeros((2, 1, 28, 28), dtype=torch.float32)
        labels = torch.zeros((2,), dtype=torch.long)
        dataset = TensorDataset(images, labels)
        empty_dataset = TensorDataset(
            torch.empty((0, 1, 28, 28), dtype=torch.float32),
            torch.empty((0,), dtype=torch.long),
        )
        return {
            "train": DataLoader(dataset, batch_size=batch_size, shuffle=False),
            "val": DataLoader(dataset, batch_size=batch_size, shuffle=False),
            "test": DataLoader(empty_dataset, batch_size=batch_size, shuffle=False),
        }


class _FineTuningPolicyFactory:
    def apply(self, model: nn.Module, profile: TrainingProfile):
        return list(model.parameters())


class _RecordingOptimizerFactory:
    def __init__(self) -> None:
        self.optimizer = None

    def build(self, profile: TrainingProfile, parameters):
        self.optimizer = torch.optim.Adam(
            list(parameters),
            lr=profile.learning_rate,
        )
        return self.optimizer


class _MetricsCalculator:
    def calculate(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        class_names: tuple[str, ...],
    ) -> dict:
        return {
            "accuracy": 1.0,
            "precisionMacro": 1.0,
            "recallMacro": 1.0,
            "f1Macro": 1.0,
            "classes": [],
            "classNames": list(class_names),
            "confusionMatrix": [[int(len(y_true))]],
        }


class _RecordingArtifactWriter:
    def __init__(self) -> None:
        self.saved_epoch_marker = None

    def write(
        self,
        model: nn.Module,
        output_model_directory_path: str,
        manifest: ModelManifest,
    ) -> str:
        self.saved_epoch_marker = int(model.epoch_marker.item())
        return manifest.artifacts.primary_artifact_relative_path


class _RecordingReportWriter:
    def __init__(self) -> None:
        self.summary = None
        self.metrics = None
        self.history = None

    def write(
        self,
        report_directory_path: str,
        summary: dict,
        metrics: dict,
        history: list[dict] | None = None,
    ) -> dict[str, str | None]:
        self.summary = summary
        self.metrics = metrics
        self.history = history or []
        return {
            "summary": "summary.json",
            "metrics": "metrics.json",
            "confusionMatrix": "confusion_matrix.json",
        }


class _DeterministicPytorchTrainingRunner(PytorchTrainingRunner):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._epoch_index = 0
        self._train_metrics = (
            {"loss": 0.6, "accuracy": 0.70},
            {"loss": 0.5, "accuracy": 0.80},
            {"loss": 0.4, "accuracy": 0.85},
            {"loss": 0.3, "accuracy": 0.90},
        )
        self._val_metrics = (
            {"loss": 0.45, "accuracy": 0.72},
            {"loss": 0.30, "accuracy": 0.84},
            {"loss": 0.31, "accuracy": 0.83},
            {"loss": 0.33, "accuracy": 0.82},
        )

    def _train_one_epoch(
        self,
        model: nn.Module,
        dataloader: DataLoader,
        optimizer: torch.optim.Optimizer,
        criterion: nn.Module,
        device: torch.device,
        cancellation_token: CancellationToken | None = None,
    ) -> dict:
        self._epoch_index += 1
        model.epoch_marker.fill_(float(self._epoch_index))
        return self._train_metrics[self._epoch_index - 1]

    def _evaluate_loss_accuracy(
        self,
        model: nn.Module,
        dataloader: DataLoader,
        criterion: nn.Module,
        device: torch.device,
        cancellation_token: CancellationToken | None = None,
    ) -> dict:
        return self._val_metrics[self._epoch_index - 1]

    def _predict(
        self,
        model: nn.Module,
        dataloader: DataLoader,
        device: torch.device,
        cancellation_token: CancellationToken | None = None,
    ) -> tuple[np.ndarray, np.ndarray, float | None]:
        return (
            np.array([0], dtype=np.int64),
            np.array([0], dtype=np.int64),
            0.1,
        )


class _CancellingDuringPredictRunner(_DeterministicPytorchTrainingRunner):
    def _predict(
        self,
        model: nn.Module,
        dataloader: DataLoader,
        device: torch.device,
        cancellation_token: CancellationToken | None = None,
    ) -> tuple[np.ndarray, np.ndarray, float | None]:
        if cancellation_token is not None:
            cancellation_token.request_cancel()
            cancellation_token.throw_if_cancelled()

        return super()._predict(
            model,
            dataloader,
            device,
            cancellation_token=cancellation_token,
        )


def _manifest() -> ModelManifest:
    return ModelManifest(
        framework="pytorch",
        architecture=ModelArchitecture(
            type="custom-cnn-v1",
            family="cnn",
            num_classes=1,
            input_channels=1,
            input_height=28,
            input_width=28,
            input_profile="default-28x28-v1",
        ),
        artifacts=ModelArtifacts(
            primary_artifact_relative_path="artifacts/model.pt",
            format="pytorch-state-dict",
        ),
        capabilities=ModelCapabilities(
            can_start_training=True,
            can_use_for_inference=True,
        ),
    )


def _context(
    root_path: Path,
    *,
    use_best_checkpoint: bool = True,
    early_stopping_patience: int = 2,
    warmup_epochs: int = 0,
) -> TrainingRunContextDto:
    base_model_directory = root_path / "base"
    base_model_directory.mkdir(parents=True, exist_ok=True)
    base_artifact_path = base_model_directory / "model.pt"
    base_artifact_path.write_text("base", encoding="utf-8")
    return TrainingRunContextDto(
        run_name="pytorch-run",
        base_model=BaseModelReferenceDto(
            name="cnn-bootstrap",
            directory_path=str(base_model_directory),
            manifest_path=str(base_model_directory / "model.json"),
            primary_artifact_path=str(base_artifact_path),
            input_profile="default-28x28-v1",
            source_type="bootstrap",
        ),
        processed_dataset=ProcessedDatasetReferenceDto(
            name="digits",
            file_path=str(root_path / "digits.npz"),
            preprocessing_profile="default-28x28-v1",
        ),
        resolved_configuration=ResolvedTrainingConfigurationDto(
            training_mode="fineTuning",
            training_profile_name="cnn-default-v1",
            augmentation_profile_name="digits-light-v1",
            benchmark_name="sudoku-benchmark-v1",
            seed=1234,
            training_parameters=TrainingParametersDto(
                epochs=5,
                learning_rate=0.1,
                batch_size=2,
                early_stopping_patience=early_stopping_patience,
                lr_scheduler_patience=1,
                lr_scheduler_factor=0.5,
                fine_tuning_policy="all",
                early_stopping_min_delta=0.01,
                warmup_epochs=warmup_epochs,
                use_best_checkpoint=use_best_checkpoint,
            ),
        ),
        output_model=OutputRegistryModelDto(
            name="pytorch-run",
            directory_path=str(root_path / "models" / "pytorch-run"),
        ),
        output_paths=TrainingOutputPathsDto(
            run_directory_path=str(root_path / "runs" / "pytorch-run"),
            report_directory_path=str(root_path / "reports" / "pytorch-run"),
            benchmark_directory_path=str(root_path / "benchmark"),
            temporary_working_directory_path=str(root_path / "tmp" / "pytorch-run"),
        ),
        model_manifest=_manifest(),
    )


class PytorchTrainingRunnerTests(unittest.IsolatedAsyncioTestCase):
    async def test_start_should_use_best_checkpoint_and_stop_early(self) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            root_path = Path(temp_directory)
            publisher = _Publisher()
            optimizer_factory = _RecordingOptimizerFactory()
            artifact_writer = _RecordingArtifactWriter()
            report_writer = _RecordingReportWriter()
            runner = _DeterministicPytorchTrainingRunner(
                event_publisher=publisher,
                cancellation_registry=CancellationRegistry(),
                utc_clock=_Clock(),
                device_setting="cpu",
                model_factory=_ModelFactory(),
                artifact_loader=_ArtifactLoader(),
                artifact_writer=artifact_writer,
                dataset_loader=_DatasetLoader(),
                dataloader_factory=_DataloaderFactory(),
                input_transform_factory=_InputTransformFactory(),
                profile_catalog=_ProfileCatalog(),
                fine_tuning_policy_factory=_FineTuningPolicyFactory(),
                optimizer_factory=optimizer_factory,
                metrics_calculator=_MetricsCalculator(),
                report_writer=report_writer,
            )

            await runner.start(_context(root_path), CancellationToken())

            progress_events = [
                event
                for event, _ in publisher.events
                if event.event_type == "progress"
            ]
            self.assertEqual(len(progress_events), 4)
            self.assertEqual(artifact_writer.saved_epoch_marker, 2)
            self.assertIsNotNone(report_writer.summary)
            self.assertEqual(report_writer.summary["epochs"], 5)
            self.assertEqual(report_writer.summary["executedEpochs"], 4)
            self.assertEqual(report_writer.summary["bestEpoch"], 2)
            self.assertTrue(report_writer.summary["stoppedEarly"])
            self.assertEqual(
                report_writer.summary["bestCheckpointMetricName"],
                "validationLoss",
            )
            self.assertEqual(report_writer.summary["earlyStoppingMinDelta"], 0.01)
            self.assertEqual(report_writer.summary["warmupEpochs"], 0)
            self.assertTrue(report_writer.summary["useBestCheckpoint"])
            self.assertTrue(
                (
                    root_path
                    / "runs"
                    / "pytorch-run"
                    / BEST_CHECKPOINT_FILE_NAME
                ).is_file()
            )
            self.assertIsNotNone(optimizer_factory.optimizer)
            self.assertAlmostEqual(
                optimizer_factory.optimizer.param_groups[0]["lr"],
                0.05,
            )

    async def test_start_should_keep_last_epoch_model_when_best_checkpoint_disabled(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            root_path = Path(temp_directory)
            artifact_writer = _RecordingArtifactWriter()
            report_writer = _RecordingReportWriter()
            runner = _DeterministicPytorchTrainingRunner(
                event_publisher=_Publisher(),
                cancellation_registry=CancellationRegistry(),
                utc_clock=_Clock(),
                device_setting="cpu",
                model_factory=_ModelFactory(),
                artifact_loader=_ArtifactLoader(),
                artifact_writer=artifact_writer,
                dataset_loader=_DatasetLoader(),
                dataloader_factory=_DataloaderFactory(),
                input_transform_factory=_InputTransformFactory(),
                profile_catalog=_ProfileCatalog(),
                fine_tuning_policy_factory=_FineTuningPolicyFactory(),
                optimizer_factory=_RecordingOptimizerFactory(),
                metrics_calculator=_MetricsCalculator(),
                report_writer=report_writer,
            )

            await runner.start(
                _context(root_path, use_best_checkpoint=False),
                CancellationToken(),
            )

            self.assertEqual(artifact_writer.saved_epoch_marker, 4)
            self.assertIsNotNone(report_writer.summary)
            self.assertFalse(report_writer.summary["useBestCheckpoint"])

    async def test_start_should_delay_early_stopping_until_after_warmup_epochs(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            root_path = Path(temp_directory)
            publisher = _Publisher()
            artifact_writer = _RecordingArtifactWriter()
            report_writer = _RecordingReportWriter()
            runner = _DeterministicPytorchTrainingRunner(
                event_publisher=publisher,
                cancellation_registry=CancellationRegistry(),
                utc_clock=_Clock(),
                device_setting="cpu",
                model_factory=_ModelFactory(),
                artifact_loader=_ArtifactLoader(),
                artifact_writer=artifact_writer,
                dataset_loader=_DatasetLoader(),
                dataloader_factory=_DataloaderFactory(),
                input_transform_factory=_InputTransformFactory(),
                profile_catalog=_ProfileCatalog(),
                fine_tuning_policy_factory=_FineTuningPolicyFactory(),
                optimizer_factory=_RecordingOptimizerFactory(),
                metrics_calculator=_MetricsCalculator(),
                report_writer=report_writer,
            )

            await runner.start(
                _context(
                    root_path,
                    early_stopping_patience=1,
                    warmup_epochs=3,
                ),
                CancellationToken(),
            )

            progress_events = [
                event
                for event, _ in publisher.events
                if event.event_type == "progress"
            ]
            self.assertEqual(len(progress_events), 4)
            self.assertEqual(artifact_writer.saved_epoch_marker, 2)
            self.assertIsNotNone(report_writer.summary)
            self.assertEqual(report_writer.summary["executedEpochs"], 4)
            self.assertEqual(report_writer.summary["bestEpoch"], 2)
            self.assertTrue(report_writer.summary["stoppedEarly"])
            self.assertEqual(report_writer.summary["warmupEpochs"], 3)

    async def test_start_should_publish_cancelled_when_cancel_requested_during_evaluation(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            root_path = Path(temp_directory)
            publisher = _Publisher()
            artifact_writer = _RecordingArtifactWriter()
            report_writer = _RecordingReportWriter()
            runner = _CancellingDuringPredictRunner(
                event_publisher=publisher,
                cancellation_registry=CancellationRegistry(),
                utc_clock=_Clock(),
                device_setting="cpu",
                model_factory=_ModelFactory(),
                artifact_loader=_ArtifactLoader(),
                artifact_writer=artifact_writer,
                dataset_loader=_DatasetLoader(),
                dataloader_factory=_DataloaderFactory(),
                input_transform_factory=_InputTransformFactory(),
                profile_catalog=_ProfileCatalog(),
                fine_tuning_policy_factory=_FineTuningPolicyFactory(),
                optimizer_factory=_RecordingOptimizerFactory(),
                metrics_calculator=_MetricsCalculator(),
                report_writer=report_writer,
            )

            await runner.start(_context(root_path), CancellationToken())

            self.assertIsNone(artifact_writer.saved_epoch_marker)
            self.assertIsNone(report_writer.summary)
            self.assertGreater(len(publisher.events), 0)
            last_event, is_terminal = publisher.events[-1]
            self.assertTrue(is_terminal)
            self.assertEqual(last_event.event_type, "cancelled")
            self.assertEqual(last_event.status, "cancelled")


if __name__ == "__main__":
    unittest.main()
