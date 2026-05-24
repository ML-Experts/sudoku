import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from application.features.trainings.dto.training_run_context_dto import (
    BaseModelReferenceDto,
    OutputRegistryModelDto,
    ProcessedDatasetReferenceDto,
    ResolvedTrainingConfigurationDto,
    TrainingParametersDto,
    TrainingOutputPathsDto,
    TrainingRunContextDto,
)
from infrastructure.training.cancellation.cancellation_token import CancellationToken
from infrastructure.training.cancellation.cancellation_registry import (
    CancellationRegistry,
)
from infrastructure.training.profiles.training_profile import TrainingProfile
from infrastructure.training.runners.mock_training_runner import MockTrainingRunner
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


class _ProfileCatalog:
    def __init__(self, epochs: int) -> None:
        self._epochs = epochs

    def create_effective_profile(
        self,
        manifest: ModelManifest,
        training_parameters: TrainingParametersDto,
        profile_name: str | None = None,
    ) -> TrainingProfile:
        return TrainingProfile(
            name=profile_name or "runtime",
            architecture_family=manifest.architecture.family,
            epochs=self._epochs,
            batch_size=training_parameters.batch_size,
            learning_rate=training_parameters.learning_rate,
            optimizer="adam",
            fine_tuning_policy=training_parameters.fine_tuning_policy,
        )


class _Clock:
    def now(self) -> datetime:
        return datetime(2026, 5, 3, 9, 30, tzinfo=UTC)


def _manifest() -> ModelManifest:
    return ModelManifest(
        framework="pytorch",
        architecture=ModelArchitecture(
            type="custom-cnn-v1",
            family="cnn",
            num_classes=10,
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
            can_use_for_inference=False,
        ),
    )


def _context(root_path: Path) -> TrainingRunContextDto:
    base_model_directory = root_path / "base"
    base_model_directory.mkdir()
    base_artifact_path = base_model_directory / "model.pt"
    base_artifact_path.write_text("base-artifact", encoding="utf-8")
    return TrainingRunContextDto(
        run_name="mock-run",
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
                epochs=3,
                learning_rate=0.001,
                batch_size=1,
                early_stopping_patience=2,
                lr_scheduler_patience=1,
                lr_scheduler_factor=0.5,
                fine_tuning_policy="all",
            ),
        ),
        output_model=OutputRegistryModelDto(
            name="mock-run",
            directory_path=str(root_path / "models" / "mock-run"),
        ),
        output_paths=TrainingOutputPathsDto(
            run_directory_path=str(root_path / "runs" / "mock-run"),
            report_directory_path=str(root_path / "reports" / "mock-run"),
            benchmark_directory_path=str(root_path / "benchmark"),
            temporary_working_directory_path=str(root_path / "tmp" / "mock-run"),
        ),
        model_manifest=_manifest(),
    )


class MockTrainingRunnerTests(unittest.IsolatedAsyncioTestCase):
    async def test_start_should_publish_progress_per_profile_epoch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            root_path = Path(temp_directory)
            publisher = _Publisher()
            runner = MockTrainingRunner(
                event_publisher=publisher,
                cancellation_registry=CancellationRegistry(),
                profile_catalog=_ProfileCatalog(epochs=3),
                utc_clock=_Clock(),
                interval_seconds=0,
            )

            await runner.start(_context(root_path), CancellationToken())

            event_types = [event.event_type for event, _ in publisher.events]
            progress_events = [
                event for event, _ in publisher.events if event.event_type == "progress"
            ]

        self.assertEqual(event_types[0], "statusChanged")
        self.assertEqual(event_types[-1], "completed")
        self.assertIn("statusChanged", event_types)
        self.assertEqual(len(progress_events), 3)
        self.assertEqual(progress_events[-1].progress.percent, 100.0)


if __name__ == "__main__":
    unittest.main()
