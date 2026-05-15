import logging
import random
from copy import deepcopy
from pathlib import Path
from time import perf_counter

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader

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
)
from models.report_status import ReportStatus
from models.training_run_event_type import TrainingRunEventType
from models.training_run_stage import TrainingRunStage
from models.training_run_status import TrainingRunStatus

LOGGER = logging.getLogger(__name__)
REPORT_MISSING_WARNING = "training_report_missing"
REPORT_CORRUPTED_WARNING = "training_report_corrupted"
BEST_CHECKPOINT_FILE_NAME = "checkpoint_best.pt"
MIN_SCHEDULER_LR = 1e-6


class PytorchTrainingRunner:
    def __init__(
        self,
        event_publisher,
        cancellation_registry,
        utc_clock,
        device_setting: str,
        model_factory,
        artifact_loader,
        artifact_writer,
        dataset_loader,
        dataloader_factory,
        input_transform_factory,
        profile_catalog,
        fine_tuning_policy_factory,
        optimizer_factory,
        metrics_calculator,
        report_writer,
    ) -> None:
        self._event_publisher = event_publisher
        self._cancellation_registry = cancellation_registry
        self._utc_clock = utc_clock
        self._device_setting = device_setting
        self._model_factory = model_factory
        self._artifact_loader = artifact_loader
        self._artifact_writer = artifact_writer
        self._dataset_loader = dataset_loader
        self._dataloader_factory = dataloader_factory
        self._input_transform_factory = input_transform_factory
        self._profile_catalog = profile_catalog
        self._fine_tuning_policy_factory = fine_tuning_policy_factory
        self._optimizer_factory = optimizer_factory
        self._metrics_calculator = metrics_calculator
        self._report_writer = report_writer

    async def start(
        self,
        context: TrainingRunContextDto,
        cancellation_token: CancellationToken,
    ) -> None:
        training_started_at = perf_counter()
        sequence = TrainingEventSequence()
        profile = self._profile_catalog.get(
            context.resolved_configuration.training_profile_name,
            context.model_manifest,
        )
        stage = TrainingRunStage.TRAINING.value
        try:
            self._seed_everything(context.resolved_configuration.seed)
            device = self._resolve_device()
            self._cancellation_registry.mark_running(context.run_name)
            await self._publish_status_changed(
                sequence,
                context,
                stage=stage,
                message="Training started.",
                epoch_total=profile.epochs,
            )

            model = self._model_factory.build(context.model_manifest).to(device)
            self._artifact_loader.load(
                model,
                context.base_model.primary_artifact_path,
                context.model_manifest,
                device,
            )
            cancellation_token.throw_if_cancelled()

            transform = self._input_transform_factory.build(
                context.model_manifest,
                context.resolved_configuration.augmentation_profile_name,
            )
            arrays = self._dataset_loader.load(
                context.processed_dataset.file_path
            )
            dataloaders = self._dataloader_factory.build(
                arrays,
                transform,
                profile.batch_size,
            )
            trainable_parameters = self._fine_tuning_policy_factory.apply(
                model,
                profile,
            )
            optimizer = self._optimizer_factory.build(
                profile,
                trainable_parameters,
            )
            criterion = nn.CrossEntropyLoss()
            scheduler = self._build_scheduler(optimizer, profile)

            history = []
            best_model_state = deepcopy(model.state_dict())
            best_monitored_loss = None
            best_monitored_accuracy = None
            best_monitored_metric_name = None
            best_epoch = 0
            executed_epochs = 0
            epochs_without_improvement = 0
            stopped_early = False
            for epoch in range(1, profile.epochs + 1):
                cancellation_token.throw_if_cancelled()
                train_metrics = self._train_one_epoch(
                    model,
                    dataloaders["train"],
                    optimizer,
                    criterion,
                    device,
                )
                val_metrics = self._evaluate_loss_accuracy(
                    model,
                    dataloaders["val"],
                    criterion,
                    device,
                )
                history.append(
                    {
                        "epoch": epoch,
                        "trainLoss": train_metrics["loss"],
                        "validationLoss": val_metrics["loss"],
                        "trainAccuracy": train_metrics["accuracy"],
                        "validationAccuracy": val_metrics["accuracy"],
                    }
                )
                self._write_checkpoint(context, model, epoch)
                (
                    monitored_loss,
                    monitored_accuracy,
                    monitored_metric_name,
                ) = self._select_monitored_metrics(train_metrics, val_metrics)
                if scheduler is not None and monitored_loss is not None:
                    scheduler.step(monitored_loss)
                if self._is_monitored_metric_improved(
                    monitored_loss=monitored_loss,
                    monitored_accuracy=monitored_accuracy,
                    best_monitored_loss=best_monitored_loss,
                    best_monitored_accuracy=best_monitored_accuracy,
                    min_delta=profile.early_stopping_min_delta,
                ):
                    best_model_state = deepcopy(model.state_dict())
                    best_monitored_loss = monitored_loss
                    best_monitored_accuracy = monitored_accuracy
                    best_monitored_metric_name = monitored_metric_name
                    best_epoch = epoch
                    epochs_without_improvement = 0
                    self._write_best_checkpoint(context, model)
                else:
                    epochs_without_improvement += 1
                executed_epochs = epoch
                await self._publish_progress(
                    sequence,
                    context,
                    epoch,
                    profile.epochs,
                    train_metrics,
                    val_metrics,
                )
                if self._should_stop_early(
                    profile,
                    epochs_without_improvement,
                ):
                    stopped_early = True
                    break

            cancellation_token.throw_if_cancelled()
            if best_epoch > 0:
                model.load_state_dict(best_model_state)
            stage = TrainingRunStage.EVALUATION.value
            evaluation_message = "Training evaluation started."
            if stopped_early:
                evaluation_message = (
                    f"Early stopping triggered at epoch {executed_epochs}. "
                    "Training evaluation started."
                )
            await self._publish_status_changed(
                sequence,
                context,
                stage=stage,
                message=evaluation_message,
                epoch_total=profile.epochs,
            )
            evaluation_loader = self._select_evaluation_loader(dataloaders)
            y_true, y_pred, average_inference_time_ms = self._predict(
                model,
                evaluation_loader,
                device,
            )
            metrics = self._metrics_calculator.calculate(
                y_true,
                y_pred,
                arrays.class_names,
            )
            cancellation_token.throw_if_cancelled()
            artifact_relative_path = self._artifact_writer.write(
                model,
                context.output_model.directory_path,
                context.model_manifest,
            )
            report_status = ReportStatus.READY.value
            warnings = ()
            try:
                report_paths = self._write_reports(
                    context,
                    profile.epochs,
                    executed_epochs=executed_epochs,
                    best_epoch=best_epoch or None,
                    stopped_early=stopped_early,
                    best_monitored_metric_name=best_monitored_metric_name,
                    best_monitored_loss=best_monitored_loss,
                    best_monitored_accuracy=best_monitored_accuracy,
                    device=device,
                    metrics=metrics,
                    history=history,
                    training_duration_seconds=round(
                        perf_counter() - training_started_at,
                        3,
                    ),
                    average_inference_time_ms=average_inference_time_ms,
                )
            except ReportCorruptedError as error:
                LOGGER.warning(
                    "Training report validation failed after model artifact was written.",
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
                    "Training report write failed after model artifact was written.",
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
            await self._publish_completed(
                sequence,
                context,
                artifact_relative_path,
                report_paths,
                report_status,
                TrainingMetricsSummaryDto(
                    accuracy=metrics.get("accuracy"),
                    macro_f1=metrics.get("f1Macro"),
                ),
                warnings=warnings,
            )
        except CancelledTrainingRun:
            await self._publish_cancelled(sequence, context)
        except Exception as error:
            await self._publish_failed(sequence, context, stage, error)
        finally:
            self._cancellation_registry.release(context.run_name)

    def _seed_everything(self, seed: int) -> None:
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)

    def _resolve_device(self) -> torch.device:
        device_setting = self._device_setting.strip().lower()
        if device_setting == "auto":
            return torch.device("cuda" if torch.cuda.is_available() else "cpu")
        if device_setting == "cpu":
            return torch.device("cpu")
        if device_setting == "cuda":
            if not torch.cuda.is_available():
                raise RuntimeError("CUDA was requested but is not available.")
            return torch.device("cuda")
        raise RuntimeError(f"Unsupported training device: {self._device_setting}")

    def _train_one_epoch(
        self,
        model: nn.Module,
        dataloader: DataLoader,
        optimizer: torch.optim.Optimizer,
        criterion: nn.Module,
        device: torch.device,
    ) -> dict:
        model.train()
        total_loss = 0.0
        total_count = 0
        correct_count = 0
        for images, labels in dataloader:
            images = images.to(device)
            labels = labels.to(device)
            optimizer.zero_grad()
            logits = model(images)
            loss = criterion(logits, labels)
            loss.backward()
            optimizer.step()
            batch_count = labels.shape[0]
            total_loss += float(loss.item()) * batch_count
            total_count += int(batch_count)
            correct_count += int((logits.argmax(dim=1) == labels).sum().item())
        return self._loss_accuracy(total_loss, total_count, correct_count)

    def _evaluate_loss_accuracy(
        self,
        model: nn.Module,
        dataloader: DataLoader,
        criterion: nn.Module,
        device: torch.device,
    ) -> dict:
        if len(dataloader.dataset) == 0:
            return {"loss": None, "accuracy": None}
        model.eval()
        total_loss = 0.0
        total_count = 0
        correct_count = 0
        with torch.no_grad():
            for images, labels in dataloader:
                images = images.to(device)
                labels = labels.to(device)
                logits = model(images)
                loss = criterion(logits, labels)
                batch_count = labels.shape[0]
                total_loss += float(loss.item()) * batch_count
                total_count += int(batch_count)
                correct_count += int(
                    (logits.argmax(dim=1) == labels).sum().item()
                )
        return self._loss_accuracy(total_loss, total_count, correct_count)

    def _loss_accuracy(
        self,
        total_loss: float,
        total_count: int,
        correct_count: int,
    ) -> dict:
        if total_count == 0:
            return {"loss": None, "accuracy": None}
        return {
            "loss": total_loss / total_count,
            "accuracy": correct_count / total_count,
        }

    def _build_scheduler(
        self,
        optimizer: torch.optim.Optimizer,
        profile,
    ) -> torch.optim.lr_scheduler.ReduceLROnPlateau | None:
        if (
            profile.lr_scheduler_patience is None
            or profile.lr_scheduler_factor is None
        ):
            return None
        return torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer,
            mode="min",
            factor=profile.lr_scheduler_factor,
            patience=profile.lr_scheduler_patience,
            min_lr=MIN_SCHEDULER_LR,
        )

    def _select_monitored_metrics(
        self,
        train_metrics: dict,
        val_metrics: dict,
    ) -> tuple[float | None, float | None, str]:
        if val_metrics["loss"] is not None:
            return (
                val_metrics["loss"],
                val_metrics["accuracy"],
                "validationLoss",
            )
        return (
            train_metrics["loss"],
            train_metrics["accuracy"],
            "trainLoss",
        )

    def _is_monitored_metric_improved(
        self,
        monitored_loss: float | None,
        monitored_accuracy: float | None,
        best_monitored_loss: float | None,
        best_monitored_accuracy: float | None,
        min_delta: float,
    ) -> bool:
        if monitored_loss is None:
            return best_monitored_loss is None
        if best_monitored_loss is None:
            return True
        if monitored_loss < best_monitored_loss - min_delta:
            return True
        if (
            abs(monitored_loss - best_monitored_loss) <= min_delta
            and monitored_accuracy is not None
            and best_monitored_accuracy is not None
        ):
            return monitored_accuracy > best_monitored_accuracy
        return False

    def _should_stop_early(
        self,
        profile,
        epochs_without_improvement: int,
    ) -> bool:
        if profile.early_stopping_patience is None:
            return False
        return epochs_without_improvement >= profile.early_stopping_patience

    def _select_evaluation_loader(
        self,
        dataloaders: dict[str, DataLoader],
    ) -> DataLoader:
        if len(dataloaders["test"].dataset) > 0:
            return dataloaders["test"]
        if len(dataloaders["val"].dataset) > 0:
            return dataloaders["val"]
        return dataloaders["train"]

    def _predict(
        self,
        model: nn.Module,
        dataloader: DataLoader,
        device: torch.device,
    ) -> tuple[np.ndarray, np.ndarray, float | None]:
        model.eval()
        y_true = []
        y_pred = []
        inference_seconds = 0.0
        inference_count = 0
        with torch.no_grad():
            for images, labels in dataloader:
                device_images = images.to(device)
                batch_started_at = perf_counter()
                logits = model(device_images)
                if device.type == "cuda":
                    torch.cuda.synchronize(device)
                inference_seconds += perf_counter() - batch_started_at
                inference_count += int(labels.shape[0])
                y_true.extend(labels.cpu().numpy().astype(np.int64).tolist())
                y_pred.extend(
                    logits.argmax(dim=1).cpu().numpy().astype(np.int64).tolist()
                )
        average_inference_time_ms = None
        if inference_count > 0:
            average_inference_time_ms = round(
                inference_seconds * 1000 / inference_count,
                4,
            )
        return (
            np.array(y_true, dtype=np.int64),
            np.array(y_pred, dtype=np.int64),
            average_inference_time_ms,
        )

    def _write_checkpoint(
        self,
        context: TrainingRunContextDto,
        model: nn.Module,
        epoch: int,
    ) -> None:
        checkpoint_directory = Path(context.output_paths.run_directory_path)
        checkpoint_directory.mkdir(parents=True, exist_ok=True)
        torch.save(
            model.state_dict(),
            checkpoint_directory / f"checkpoint_epoch_{epoch}.pt",
        )

    def _write_best_checkpoint(
        self,
        context: TrainingRunContextDto,
        model: nn.Module,
    ) -> None:
        checkpoint_directory = Path(context.output_paths.run_directory_path)
        checkpoint_directory.mkdir(parents=True, exist_ok=True)
        torch.save(
            model.state_dict(),
            checkpoint_directory / BEST_CHECKPOINT_FILE_NAME,
        )

    def _write_reports(
        self,
        context: TrainingRunContextDto,
        epoch_total: int,
        executed_epochs: int,
        best_epoch: int | None,
        stopped_early: bool,
        best_monitored_metric_name: str | None,
        best_monitored_loss: float | None,
        best_monitored_accuracy: float | None,
        device: torch.device,
        metrics: dict,
        history: list[dict],
        training_duration_seconds: float,
        average_inference_time_ms: float | None,
    ) -> dict[str, str | None]:
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
            "epochs": epoch_total,
            "executedEpochs": executed_epochs,
            "bestEpoch": best_epoch,
            "stoppedEarly": stopped_early,
            "bestCheckpointMetricName": best_monitored_metric_name,
            "bestMonitoredLoss": best_monitored_loss,
            "bestMonitoredAccuracy": best_monitored_accuracy,
            "device": str(device),
            "trainingDurationSeconds": training_duration_seconds,
            "averageInferenceTimeMs": average_inference_time_ms,
        }
        return self._report_writer.write(
            context.output_paths.report_directory_path,
            summary,
            metrics,
            history,
        )

    async def _publish_status_changed(
        self,
        sequence: TrainingEventSequence,
        context: TrainingRunContextDto,
        stage: str,
        message: str,
        epoch_total: int,
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
        train_metrics: dict,
        val_metrics: dict,
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
                    train_loss=train_metrics["loss"],
                    validation_loss=val_metrics["loss"],
                    train_accuracy=train_metrics["accuracy"],
                    validation_accuracy=val_metrics["accuracy"],
                ),
                warnings=(),
                result=None,
                failure=None,
            )
        )

    async def _publish_completed(
        self,
        sequence: TrainingEventSequence,
        context: TrainingRunContextDto,
        artifact_relative_path: str,
        report_paths: dict[str, str | None],
        report_status: str,
        metrics_summary: TrainingMetricsSummaryDto | None,
        warnings: tuple[str, ...],
    ) -> None:
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
                    metrics_summary=metrics_summary,
                    summary_relative_path=report_paths.get("summary"),
                    metrics_relative_path=report_paths.get("metrics"),
                    confusion_matrix_relative_path=report_paths.get(
                        "confusionMatrix"
                    ),
                ),
                failure=None,
            ),
            terminal=True,
        )

    async def _publish_cancelled(
        self,
        sequence: TrainingEventSequence,
        context: TrainingRunContextDto,
    ) -> None:
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

    async def _publish_failed(
        self,
        sequence: TrainingEventSequence,
        context: TrainingRunContextDto,
        stage: str,
        error: Exception,
    ) -> None:
        await self._event_publisher.publish(
            TrainingRunEventDto(
                event_type=TrainingRunEventType.FAILED.value,
                sequence=sequence.next(),
                run_name=context.run_name,
                status=TrainingRunStatus.FAILED.value,
                stage=stage,
                occurred_at_utc=self._utc_clock.now(),
                message=str(error) or "Training failed.",
                progress=None,
                warnings=(),
                result=None,
                failure=TrainingRunFailureDto(
                    error_type="training_run_failed",
                    message=str(error) or "Training failed.",
                    can_use_produced_model_for_inference=False,
                ),
            ),
            terminal=True,
        )
