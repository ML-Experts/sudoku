import asyncio
import unittest
from datetime import UTC, datetime
from unittest.mock import patch

from application.features.trainings.dto.training_run_event_dto import (
    TrainingRunEventDto,
    TrainingMetricsSummaryDto,
    TrainingRunProgressDto,
    TrainingRunResultDto,
)
from infrastructure.training.events.backend_training_event_publisher import (
    BackendTrainingEventPublisher,
)


def _progress_event(sequence: int = 5) -> TrainingRunEventDto:
    return TrainingRunEventDto(
        event_type="progress",
        sequence=sequence,
        run_name="train-1",
        status="running",
        stage="training",
        occurred_at_utc=datetime(2026, 5, 3, 9, 30, tzinfo=UTC),
        message="Epoch 2/3.",
        progress=TrainingRunProgressDto(
            percent=66.67,
            epoch_current=2,
            epoch_total=3,
            train_loss=0.2,
            validation_loss=0.3,
            train_accuracy=0.8,
            validation_accuracy=0.7,
        ),
        warnings=(),
        result=None,
        failure=None,
    )


class _FakeResponse:
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code


class _FakeAsyncClient:
    calls: list[dict] = []
    statuses: list[int] = []

    def __init__(self, timeout: float) -> None:
        self.timeout = timeout

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        return None

    async def post(self, url: str, json: dict):
        self.calls.append({"url": url, "json": json})
        return _FakeResponse(self.statuses.pop(0))


class BackendTrainingEventPublisherTests(unittest.TestCase):
    def test_to_payload_should_serialize_progress_metrics_as_camel_case(self) -> None:
        publisher = BackendTrainingEventPublisher(
            backend_base_url="http://backend",
            timeout_seconds=5,
            terminal_event_retry_delay_seconds=0,
            terminal_event_max_attempts=1,
            active_event_max_attempts=1,
        )

        payload = publisher._to_payload(_progress_event())

        self.assertEqual(payload["eventType"], "progress")
        self.assertEqual(payload["occurredAtUtc"], "2026-05-03T09:30:00Z")
        self.assertEqual(payload["progress"]["epochTotal"], 3)
        self.assertEqual(payload["progress"]["trainLoss"], 0.2)
        self.assertEqual(payload["progress"]["validationAccuracy"], 0.7)

    def test_to_payload_should_serialize_completed_result_for_be(self) -> None:
        publisher = BackendTrainingEventPublisher(
            backend_base_url="http://backend",
            timeout_seconds=5,
            terminal_event_retry_delay_seconds=0,
            terminal_event_max_attempts=1,
            active_event_max_attempts=1,
        )
        base_event = _progress_event()
        event = TrainingRunEventDto(
            event_type="completed",
            sequence=base_event.sequence,
            run_name=base_event.run_name,
            status="succeeded",
            stage="finished",
            occurred_at_utc=base_event.occurred_at_utc,
            message="Training finished.",
            progress=None,
            warnings=(),
            result=TrainingRunResultDto(
                produced_model_name="train-1",
                report_status="ready",
                can_use_produced_model_for_inference=True,
                primary_artifact_relative_path="artifacts/model.pt",
                metrics_summary=TrainingMetricsSummaryDto(
                    accuracy=0.9,
                    macro_f1=0.8,
                ),
                summary_relative_path="summary.json",
                metrics_relative_path="metrics.json",
                confusion_matrix_relative_path="confusion_matrix.json",
            ),
            failure=None,
        )

        payload = publisher._to_payload(event)

        self.assertEqual(payload["result"]["reportStatus"], "ready")
        self.assertEqual(
            payload["result"]["primaryArtifactRelativePath"],
            "artifacts/model.pt",
        )
        self.assertEqual(payload["result"]["metricsSummary"]["macroF1"], 0.8)

    def test_publish_should_retry_terminal_event_with_same_payload(self) -> None:
        publisher = BackendTrainingEventPublisher(
            backend_base_url="http://backend",
            timeout_seconds=5,
            terminal_event_retry_delay_seconds=0,
            terminal_event_max_attempts=2,
            active_event_max_attempts=1,
        )
        event = _progress_event(sequence=9)
        event = TrainingRunEventDto(
            event_type="completed",
            sequence=event.sequence,
            run_name=event.run_name,
            status="succeeded",
            stage="finished",
            occurred_at_utc=event.occurred_at_utc,
            message="Training finished.",
            progress=None,
            warnings=(),
            result=None,
            failure=None,
        )
        _FakeAsyncClient.calls = []
        _FakeAsyncClient.statuses = [500, 202]

        with patch(
            "infrastructure.training.events.backend_training_event_publisher."
            "httpx.AsyncClient",
            _FakeAsyncClient,
        ):
            asyncio.run(publisher.publish(event, terminal=True))

        self.assertEqual(len(_FakeAsyncClient.calls), 2)
        self.assertEqual(
            _FakeAsyncClient.calls[0]["json"],
            _FakeAsyncClient.calls[1]["json"],
        )
        self.assertEqual(_FakeAsyncClient.calls[0]["json"]["sequence"], 9)
        self.assertEqual(
            _FakeAsyncClient.calls[0]["url"],
            "http://backend/internal/ml/trainings/train-1/events",
        )


if __name__ == "__main__":
    unittest.main()
