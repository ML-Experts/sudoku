import asyncio
import logging
import shutil
from pathlib import Path

from application.features.trainings.dto.training_run_context_dto import (
    TrainingRunContextDto,
)
from application.features.trainings.dto.training_run_event_dto import (
    TrainingRunEventDto,
    TrainingRunFailureDto,
    TrainingMetricsSummaryDto,
    TrainingRunProgressDto,
    TrainingRunResultDto,
)
from application.features.trainings.services.training_event_sequence import (
    TrainingEventSequence,
)
from infrastructure.training.cancellation.cancellation_token import (
    CancellationToken,
    CancelledTrainingRun,
)
from infrastructure.training.reporting.training_report_writer import (
    ReportCorruptedError,
    TrainingReportWriter,
)
from models.report_status import ReportStatus
from models.training_run_event_type import TrainingRunEventType
from models.training_run_stage import TrainingRunStage
from models.training_run_status import TrainingRunStatus

LOGGER = logging.getLogger(__name__)
REPORT_MISSING_WARNING = "training_report_missing"
REPORT_CORRUPTED_WARNING = "training_report_corrupted"


class MockTrainingRunner:
    def __init__(
        self,
        event_publisher,
        cancellation_registry,
        profile_catalog,
        utc_clock,
        interval_seconds: float,
        report_writer: TrainingReportWriter | None = None,
    ) -> None:
        self._event_publisher = event_publisher
        self._cancellation_registry = cancellation_registry
        self._profile_catalog = profile_catalog
        self._utc_clock = utc_clock
        self._interval_seconds = interval_seconds
        self._report_writer = report_writer or TrainingReportWriter()

    async def start(
        self,
        context: TrainingRunContextDto,
        cancellation_token: CancellationToken,
    ) -> None:
        sequence = TrainingEventSequence()
        profile = self._profile_catalog.create_effective_profile(
            context.model_manifest,
            context.resolved_configuration.training_parameters,
            profile_name=context.resolved_configuration.training_profile_name,
        )
        try:
            self._cancellation_registry.mark_running(context.run_name)
            await self._publish_status_changed(
                sequence,
                context,
                profile.epochs,
                stage=TrainingRunStage.TRAINING.value,
                message="Training started.",
            )
            for epoch in range(1, profile.epochs + 1):
                cancellation_token.throw_if_cancelled()
                if self._interval_seconds > 0:
                    await asyncio.sleep(self._interval_seconds)
                await self._publish_progress(sequence, context, epoch, profile.epochs)

            cancellation_token.throw_if_cancelled()
            await self._publish_status_changed(
                sequence,
                context,
                profile.epochs,
                stage=TrainingRunStage.EVALUATION.value,
                message="Training evaluation started.",
            )
            artifact_relative_path = self._write_artifacts(context)
            report_status = ReportStatus.READY.value
            warnings = ()
            try:
                report_paths = self._write_reports(context, profile.epochs)
            except ReportCorruptedError as error:
                LOGGER.warning(
                    "Mock training report validation failed after artifact write.",
                    extra={
                        "run_name": context.run_name,
                        "error_type": type(error).__name__,
                    },
                )
                report_status = ReportStatus.CORRUPTED.value
                warnings = (REPORT_CORRUPTED_WARNING,)
                report_paths = {
                    "summary": None,
                    "metrics": None,
                    "confusionMatrix": None,
                }
            except Exception as error:
                LOGGER.warning(
                    "Mock training report write failed after artifact write.",
                    extra={
                        "run_name": context.run_name,
                        "error_type": type(error).__name__,
                    },
                )
                report_status = ReportStatus.MISSING.value
                warnings = (REPORT_MISSING_WARNING,)
                report_paths = {
                    "summary": None,
                    "metrics": None,
                    "confusionMatrix": None,
                }
            await self._event_publisher.publish(
                TrainingRunEventDto(
                    event_type=TrainingRunEventType.COMPLETED.value,
                    sequence=sequence.next(),
                    run_name=context.run_name,
                    status=TrainingRunStatus.SUCCEEDED.value,
                    stage=TrainingRunStage.FINISHED.value,
                    occurred_at_utc=self._utc_clock.now(),
                    message="Training finished.",
                    progress=None,
                    warnings=warnings,
                    result=TrainingRunResultDto(
                        produced_model_name=context.output_model.name,
                        report_status=report_status,
                        can_use_produced_model_for_inference=True,
                        primary_artifact_relative_path=artifact_relative_path,
                        metrics_summary=TrainingMetricsSummaryDto(
                            accuracy=0.0,
                            macro_f1=0.0,
                        ),
                        summary_relative_path=report_paths["summary"],
                        metrics_relative_path=report_paths["metrics"],
                        confusion_matrix_relative_path=(
                            report_paths["confusionMatrix"]
                        ),
                    ),
                    failure=None,
                ),
                terminal=True,
            )
        except CancelledTrainingRun:
            await self._event_publisher.publish(
                TrainingRunEventDto(
                    event_type=TrainingRunEventType.CANCELLED.value,
                    sequence=sequence.next(),
                    run_name=context.run_name,
                    status=TrainingRunStatus.CANCELLED.value,
                    stage=TrainingRunStage.FINISHED.value,
                    occurred_at_utc=self._utc_clock.now(),
                    message="Training cancelled on user request.",
                    progress=None,
                    warnings=(),
                    result=None,
                    failure=None,
                ),
                terminal=True,
            )
        except Exception as error:
            await self._publish_failed(sequence, context, error)
        finally:
            self._cancellation_registry.release(context.run_name)

    async def _publish_status_changed(
        self,
        sequence: TrainingEventSequence,
        context: TrainingRunContextDto,
        epoch_total: int,
        stage: str,
        message: str,
    ) -> None:
        await self._event_publisher.publish(
            TrainingRunEventDto(
                event_type=TrainingRunEventType.STATUS_CHANGED.value,
                sequence=sequence.next(),
                run_name=context.run_name,
                status=TrainingRunStatus.RUNNING.value,
                stage=stage,
                occurred_at_utc=self._utc_clock.now(),
                message=message,
                progress=TrainingRunProgressDto(
                    percent=0.0,
                    epoch_current=0,
                    epoch_total=epoch_total,
                ),
                warnings=(),
                result=None,
                failure=None,
            )
        )

    async def _publish_progress(
        self,
        sequence: TrainingEventSequence,
        context: TrainingRunContextDto,
        epoch: int,
        epoch_total: int,
    ) -> None:
        await self._event_publisher.publish(
            TrainingRunEventDto(
                event_type=TrainingRunEventType.PROGRESS.value,
                sequence=sequence.next(),
                run_name=context.run_name,
                status=TrainingRunStatus.RUNNING.value,
                stage=TrainingRunStage.TRAINING.value,
                occurred_at_utc=self._utc_clock.now(),
                message=f"Epoch {epoch}/{epoch_total}.",
                progress=TrainingRunProgressDto(
                    percent=round(epoch / epoch_total * 100, 2),
                    epoch_current=epoch,
                    epoch_total=epoch_total,
                    train_loss=None,
                    validation_loss=None,
                    train_accuracy=None,
                    validation_accuracy=None,
                ),
                warnings=(),
                result=None,
                failure=None,
            )
        )

    def _write_artifacts(self, context: TrainingRunContextDto) -> str:
        relative_path = context.model_manifest.artifacts.primary_artifact_relative_path
        output_path = Path(context.output_model.directory_path) / relative_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(context.base_model.primary_artifact_path, output_path)
        return relative_path

    def _write_reports(
        self,
        context: TrainingRunContextDto,
        epoch_total: int,
    ) -> dict[str, str]:
        summary = {
            "runName": context.run_name,
            "baseModelName": context.base_model.name,
            "processedDatasetName": context.processed_dataset.name,
            "producedModelName": context.output_model.name,
            "architectureType": context.model_manifest.architecture.type,
            "trainingProfileName": (
                context.resolved_configuration.training_profile_name
            ),
            "augmentationProfileName": (
                context.resolved_configuration.augmentation_profile_name
            ),
            "benchmarkName": context.resolved_configuration.benchmark_name,
            "seed": context.resolved_configuration.seed,
            "learningRate": context.resolved_configuration.training_parameters.learning_rate,
            "batchSize": context.resolved_configuration.training_parameters.batch_size,
            "earlyStoppingPatience": (
                context.resolved_configuration.training_parameters.early_stopping_patience
            ),
            "earlyStoppingMinDelta": (
                context.resolved_configuration.training_parameters.early_stopping_min_delta
            ),
            "warmupEpochs": (
                context.resolved_configuration.training_parameters.warmup_epochs
            ),
            "lrSchedulerPatience": (
                context.resolved_configuration.training_parameters.lr_scheduler_patience
            ),
            "lrSchedulerFactor": (
                context.resolved_configuration.training_parameters.lr_scheduler_factor
            ),
            "fineTuningPolicy": (
                context.resolved_configuration.training_parameters.fine_tuning_policy
            ),
            "useBestCheckpoint": (
                context.resolved_configuration.training_parameters.use_best_checkpoint
            ),
            "epochs": epoch_total,
            "device": "mock",
            "runner": "mock",
            "trainingDurationSeconds": 0.0,
            "averageInferenceTimeMs": 0.0,
        }
        metrics = {
            "runName": context.run_name,
            "accuracy": 0.0,
            "precisionMacro": 0.0,
            "recallMacro": 0.0,
            "f1Macro": 0.0,
            "classes": [],
            "classNames": [],
            "confusionMatrix": [],
        }
        history = tuple(
            {
                "epoch": epoch,
                "trainLoss": None,
                "validationLoss": None,
                "trainAccuracy": None,
                "validationAccuracy": None,
            }
            for epoch in range(1, epoch_total + 1)
        )
        return self._report_writer.write(
            context.output_paths.report_directory_path,
            summary,
            metrics,
            list(history),
        )

    async def _publish_failed(
        self,
        sequence: TrainingEventSequence,
        context: TrainingRunContextDto,
        error: Exception,
    ) -> None:
        message = str(error) or "Training failed."
        await self._event_publisher.publish(
            TrainingRunEventDto(
                event_type=TrainingRunEventType.FAILED.value,
                sequence=sequence.next(),
                run_name=context.run_name,
                status=TrainingRunStatus.FAILED.value,
                stage=TrainingRunStage.FINISHED.value,
                occurred_at_utc=self._utc_clock.now(),
                message=message,
                progress=None,
                warnings=(),
                result=None,
                failure=TrainingRunFailureDto(
                    error_type="training_run_failed",
                    message=message,
                    can_use_produced_model_for_inference=False,
                ),
            ),
            terminal=True,
        )
