from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class TrainingRunProgressDto:
    percent: float | None
    epoch_current: int | None
    epoch_total: int | None
    train_loss: float | None = None
    validation_loss: float | None = None
    train_accuracy: float | None = None
    validation_accuracy: float | None = None
    eta_seconds: int | None = None


@dataclass(frozen=True)
class TrainingMetricsSummaryDto:
    accuracy: float | None
    macro_f1: float | None


@dataclass(frozen=True)
class TrainingRunResultDto:
    produced_model_name: str
    report_status: str
    can_use_produced_model_for_inference: bool
    primary_artifact_relative_path: str
    metrics_summary: TrainingMetricsSummaryDto | None
    summary_relative_path: str | None
    metrics_relative_path: str | None
    confusion_matrix_relative_path: str | None


@dataclass(frozen=True)
class TrainingRunFailureDto:
    error_type: str
    message: str
    can_use_produced_model_for_inference: bool


@dataclass(frozen=True)
class TrainingRunEventDto:
    event_type: str
    sequence: int
    run_name: str
    status: str
    stage: str
    occurred_at_utc: datetime
    message: str | None
    progress: TrainingRunProgressDto | None
    warnings: tuple[str, ...]
    result: TrainingRunResultDto | None
    failure: TrainingRunFailureDto | None
