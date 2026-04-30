import asyncio
import json
import shutil
from pathlib import Path

from application.features.trainings.dto.training_run_context_dto import (
    TrainingRunContextDto,
)
from application.features.trainings.dto.training_run_event_dto import (
    TrainingRunEventDto,
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
from models.report_status import ReportStatus
from models.training_run_event_type import TrainingRunEventType
from models.training_run_stage import TrainingRunStage
from models.training_run_status import TrainingRunStatus


class MockTrainingRunner:
    def __init__(
        self,
        event_publisher,
        cancellation_registry,
        profile_catalog,
        utc_clock,
        interval_seconds: float,
    ) -> None:
        self._event_publisher = event_publisher
        self._cancellation_registry = cancellation_registry
        self._profile_catalog = profile_catalog
        self._utc_clock = utc_clock
        self._interval_seconds = interval_seconds

    async def start(
        self,
        context: TrainingRunContextDto,
        cancellation_token: CancellationToken,
    ) -> None:
        sequence = TrainingEventSequence()
        profile = self._profile_catalog.get(
            context.resolved_configuration.training_profile_name,
            context.model_manifest,
        )
        try:
            self._cancellation_registry.mark_running(context.run_name)
            await self._publish_status_changed(sequence, context, profile.epochs)
            for epoch in range(1, profile.epochs + 1):
                cancellation_token.throw_if_cancelled()
                if self._interval_seconds > 0:
                    await asyncio.sleep(self._interval_seconds)
                await self._publish_progress(sequence, context, epoch, profile.epochs)

            artifact_relative_path = self._write_artifacts(context)
            report_paths = self._write_reports(context, profile.epochs)
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
                    warnings=(),
                    result=TrainingRunResultDto(
                        produced_model_name=context.output_model.name,
                        report_status=ReportStatus.OK.value,
                        can_use_produced_model_for_inference=True,
                        primary_artifact_relative_path=artifact_relative_path,
                        report_relative_path=report_paths["summary"],
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
        finally:
            self._cancellation_registry.release(context.run_name)

    async def _publish_status_changed(
        self,
        sequence: TrainingEventSequence,
        context: TrainingRunContextDto,
        epoch_total: int,
    ) -> None:
        await self._event_publisher.publish(
            TrainingRunEventDto(
                event_type=TrainingRunEventType.STATUS_CHANGED.value,
                sequence=sequence.next(),
                run_name=context.run_name,
                status=TrainingRunStatus.RUNNING.value,
                stage=TrainingRunStage.TRAINING.value,
                occurred_at_utc=self._utc_clock.now(),
                message="Training started.",
                progress=TrainingRunProgressDto(
                    percent=0.0,
                    epoch=0,
                    total_epochs=epoch_total,
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
                    percent=epoch / epoch_total * 100,
                    epoch=epoch,
                    total_epochs=epoch_total,
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
        report_directory = Path(context.output_paths.report_directory_path)
        report_directory.mkdir(parents=True, exist_ok=True)
        summary = {
            "runName": context.run_name,
            "baseModelName": context.base_model.name,
            "processedDatasetName": context.processed_dataset.name,
            "architectureType": context.model_manifest.architecture.type,
            "trainingProfileName": (
                context.resolved_configuration.training_profile_name
            ),
            "augmentationProfileName": (
                context.resolved_configuration.augmentation_profile_name
            ),
            "seed": context.resolved_configuration.seed,
            "epochs": epoch_total,
            "runner": "mock",
        }
        metrics = {
            "accuracy": 0.0,
            "precisionMacro": 0.0,
            "recallMacro": 0.0,
            "f1Macro": 0.0,
            "perClass": [],
            "classNames": [],
            "confusionMatrix": [],
        }
        (report_directory / "summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (report_directory / "metrics.json").write_text(
            json.dumps(metrics, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (report_directory / "confusion_matrix.json").write_text(
            json.dumps({"classNames": [], "matrix": []}, indent=2),
            encoding="utf-8",
        )
        return {
            "summary": "summary.json",
            "metrics": "metrics.json",
            "confusionMatrix": "confusion_matrix.json",
        }
