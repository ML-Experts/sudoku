import asyncio

import httpx

from application.features.trainings.dto.training_run_event_dto import (
    TrainingRunEventDto,
)


class BackendTrainingEventPublisher:
    def __init__(
        self,
        backend_base_url: str,
        timeout_seconds: float,
        terminal_event_retry_delay_seconds: float,
        terminal_event_max_attempts: int,
        active_event_max_attempts: int,
    ) -> None:
        self._backend_base_url = backend_base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._terminal_event_retry_delay_seconds = (
            terminal_event_retry_delay_seconds
        )
        self._terminal_event_max_attempts = terminal_event_max_attempts
        self._active_event_max_attempts = max(1, active_event_max_attempts)

    async def publish(
        self,
        event: TrainingRunEventDto,
        *,
        terminal: bool = False,
    ) -> None:
        max_attempts = (
            self._terminal_event_max_attempts
            if terminal
            else self._active_event_max_attempts
        )
        attempt = 0
        while True:
            attempt += 1
            try:
                async with httpx.AsyncClient(
                    timeout=self._timeout_seconds
                ) as client:
                    response = await client.post(
                        (
                            f"{self._backend_base_url}/internal/ml/trainings/"
                            f"{event.run_name}/events"
                        ),
                        json=self._to_payload(event),
                    )
                if 200 <= response.status_code < 300:
                    return
            except httpx.HTTPError:
                pass

            if not terminal or (max_attempts > 0 and attempt >= max_attempts):
                return
            await asyncio.sleep(self._terminal_event_retry_delay_seconds)

    def _to_payload(self, event: TrainingRunEventDto) -> dict:
        return {
            "eventType": event.event_type,
            "sequence": event.sequence,
            "runName": event.run_name,
            "status": event.status,
            "stage": event.stage,
            "occurredAtUtc": event.occurred_at_utc.isoformat(),
            "message": event.message,
            "progress": self._progress_payload(event),
            "warnings": list(event.warnings),
            "result": self._result_payload(event),
            "failure": self._failure_payload(event),
        }

    def _progress_payload(self, event: TrainingRunEventDto) -> dict | None:
        if event.progress is None:
            return None
        return {
            "percent": event.progress.percent,
            "epoch": event.progress.epoch,
            "totalEpochs": event.progress.total_epochs,
            "trainLoss": event.progress.train_loss,
            "validationLoss": event.progress.validation_loss,
            "trainAccuracy": event.progress.train_accuracy,
            "validationAccuracy": event.progress.validation_accuracy,
            "etaSeconds": event.progress.eta_seconds,
        }

    def _result_payload(self, event: TrainingRunEventDto) -> dict | None:
        if event.result is None:
            return None
        return {
            "producedModelName": event.result.produced_model_name,
            "reportStatus": event.result.report_status,
            "reportRelativePath": event.result.report_relative_path,
            "metricsSummary": self._metrics_summary_payload(event),
            "canUseProducedModelForInference": (
                event.result.can_use_produced_model_for_inference
            ),
            "primaryArtifactRelativePath": (
                event.result.primary_artifact_relative_path
            ),
            "summaryRelativePath": event.result.summary_relative_path,
            "metricsRelativePath": event.result.metrics_relative_path,
            "confusionMatrixRelativePath": (
                event.result.confusion_matrix_relative_path
            ),
        }

    def _metrics_summary_payload(
        self, event: TrainingRunEventDto
    ) -> dict | None:
        if event.result is None or event.result.metrics_summary is None:
            return None
        return {
            "accuracy": event.result.metrics_summary.accuracy,
            "macroF1": event.result.metrics_summary.macro_f1,
        }

    def _failure_payload(self, event: TrainingRunEventDto) -> dict | None:
        if event.failure is None:
            return None
        return {
            "errorType": event.failure.error_type,
            "message": event.failure.message,
            "canUseProducedModelForInference": (
                event.failure.can_use_produced_model_for_inference
            ),
        }
