from api.config.runtime_settings import TrainingSettings
from infrastructure.training.cancellation.cancellation_registry import (
    CancellationRegistry,
)
from infrastructure.training.data.digit_dataloader_factory import (
    DigitDataloaderFactory,
)
from infrastructure.training.data.input_transform_factory import (
    InputTransformFactory,
)
from infrastructure.training.data.npz_digit_dataset import NpzDigitDatasetLoader
from infrastructure.training.events.backend_training_event_publisher import (
    BackendTrainingEventPublisher,
)
from infrastructure.training.model.model_artifact_loader import (
    ModelArtifactLoader,
)
from infrastructure.training.model.model_artifact_writer import (
    ModelArtifactWriter,
)
from infrastructure.training.model.model_factory import ModelFactory
from infrastructure.training.profiles.fine_tuning_policy_factory import (
    FineTuningPolicyFactory,
)
from infrastructure.training.profiles.optimizer_factory import OptimizerFactory
from infrastructure.training.profiles.training_profile_catalog import (
    TrainingProfileCatalog,
)
from infrastructure.training.reporting.metrics_calculator import MetricsCalculator
from infrastructure.training.reporting.training_report_writer import (
    TrainingReportWriter,
)
from infrastructure.training.runners.mock_training_runner import MockTrainingRunner
from infrastructure.training.runners.pytorch_training_runner import (
    PytorchTrainingRunner,
)


class TrainingRunnerFactory:
    def __init__(
        self,
        settings: TrainingSettings,
        cancellation_registry: CancellationRegistry,
        utc_clock,
    ) -> None:
        self._settings = settings
        self._cancellation_registry = cancellation_registry
        self._utc_clock = utc_clock

    def create(self):
        event_publisher = BackendTrainingEventPublisher(
            backend_base_url=self._settings.backend_base_url,
            timeout_seconds=self._settings.event_timeout_seconds,
            terminal_event_retry_delay_seconds=(
                self._settings.terminal_event_retry_delay_seconds
            ),
            terminal_event_max_attempts=(
                self._settings.terminal_event_max_attempts
            ),
            active_event_max_attempts=self._settings.active_event_max_attempts,
        )

        runner_name = self._settings.runner.strip().lower()
        profile_catalog = TrainingProfileCatalog(
            max_epochs_override=self._settings.max_epochs_override
        )
        if runner_name == "mock":
            return MockTrainingRunner(
                event_publisher=event_publisher,
                cancellation_registry=self._cancellation_registry,
                profile_catalog=profile_catalog,
                utc_clock=self._utc_clock,
                interval_seconds=self._settings.mock_interval_seconds,
                report_writer=TrainingReportWriter(),
            )
        if runner_name == "pytorch":
            return PytorchTrainingRunner(
                event_publisher=event_publisher,
                cancellation_registry=self._cancellation_registry,
                utc_clock=self._utc_clock,
                device_setting=self._settings.device,
                model_factory=ModelFactory(),
                artifact_loader=ModelArtifactLoader(),
                artifact_writer=ModelArtifactWriter(),
                dataset_loader=NpzDigitDatasetLoader(),
                dataloader_factory=DigitDataloaderFactory(),
                input_transform_factory=InputTransformFactory(),
                profile_catalog=profile_catalog,
                fine_tuning_policy_factory=FineTuningPolicyFactory(),
                optimizer_factory=OptimizerFactory(),
                metrics_calculator=MetricsCalculator(),
                report_writer=TrainingReportWriter(),
            )

        raise ValueError(f"Unsupported training runner: {self._settings.runner}")
