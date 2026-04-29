import asyncio
import hashlib
import json
import os
import random
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urljoin

import httpx
from fastapi import APIRouter, BackgroundTasks, status

from api.models.error_api_response import ErrorApiResponse
from api.models.training_api_models import (
    AcceptedTrainingApiResponse,
    CancelTrainingApiEntry,
    CancelTrainingApiResponse,
    StartTrainingApiEntry,
)

trainings_controller = APIRouter(prefix="/ml/trainings", tags=["trainings"])

BACKEND_BASE_URL_ENV = "ML_TRAINING_MOCK_BACKEND_BASE_URL"
INTERVAL_SECONDS_ENV = "ML_TRAINING_MOCK_INTERVAL_SECONDS"
CALLBACK_TIMEOUT_SECONDS_ENV = "ML_TRAINING_MOCK_CALLBACK_TIMEOUT_SECONDS"
CALLBACK_MAX_ATTEMPTS_ENV = "ML_TRAINING_MOCK_CALLBACK_MAX_ATTEMPTS"
CALLBACK_RETRY_DELAY_SECONDS_ENV = "ML_TRAINING_MOCK_CALLBACK_RETRY_DELAY_SECONDS"
DEFAULT_BACKEND_BASE_URL = "http://127.0.0.1:5000"
DEFAULT_INTERVAL_SECONDS = 0.75
DEFAULT_CALLBACK_TIMEOUT_SECONDS = 30.0
DEFAULT_CALLBACK_MAX_ATTEMPTS = 5
DEFAULT_CALLBACK_RETRY_DELAY_SECONDS = 1.0
MODEL_ARTIFACT_FILE_NAME = "model.keras"
REPORT_FILE_NAME = "report.json"

_cancel_requested_run_names: set[str] = set()
_terminal_run_statuses: dict[str, str] = {}


@trainings_controller.post(
    "",
    response_model=AcceptedTrainingApiResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={500: {"model": ErrorApiResponse}},
)
async def start_training(
    entry: StartTrainingApiEntry,
    background_tasks: BackgroundTasks,
) -> AcceptedTrainingApiResponse:
    accepted_at_utc = datetime.now(UTC)
    ml_job_id = f"mock-{entry.run_name}"
    _cancel_requested_run_names.discard(entry.run_name)
    _terminal_run_statuses.pop(entry.run_name, None)

    background_tasks.add_task(_run_mock_training, entry)

    return AcceptedTrainingApiResponse(
        accepted=True,
        accepted_at_utc=accepted_at_utc,
        ml_job_id=ml_job_id,
    )


@trainings_controller.post(
    "/{run_name}/cancel",
    response_model=CancelTrainingApiResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def cancel_training(
    run_name: str,
    entry: CancelTrainingApiEntry,
) -> CancelTrainingApiResponse:
    if entry.run_name != run_name:
        return CancelTrainingApiResponse(
            accepted=False,
            run_name=run_name,
            status=None,
            disposition="run_name_mismatch",
        )

    terminal_status = _terminal_run_statuses.get(run_name)
    if terminal_status is not None:
        return CancelTrainingApiResponse(
            accepted=True,
            run_name=run_name,
            status=terminal_status,
            disposition="already_finished",
        )

    _cancel_requested_run_names.add(run_name)
    return CancelTrainingApiResponse(
        accepted=True,
        run_name=run_name,
        status="cancelling",
        disposition="accepted",
    )


async def _run_mock_training(entry: StartTrainingApiEntry) -> None:
    interval_seconds = _get_interval_seconds()
    randomizer = random.Random(_stable_seed(entry.run_name, entry.training.seed))

    _ensure_runtime_directories(entry)

    for sequence in range(1, 8):
        await _sleep(interval_seconds)
        if await _post_cancelled_if_requested(entry, sequence, randomizer):
            return

        event_type = "statusChanged" if sequence == 1 else "progress"
        epoch = max(0, sequence - 1)
        percent = round((sequence / 8) * 100, 1)
        await _post_event(
            entry,
            sequence=sequence,
            event_type=event_type,
            status_value="running",
            message=f"Mock ML processed step {sequence}/8.",
            progress=_build_progress(
                percent=percent,
                epoch=epoch,
                total_epochs=7,
                randomizer=randomizer,
            ),
        )

    if await _post_cancelled_if_requested(entry, 8, randomizer):
        return

    metrics = _write_success_artifacts(entry, randomizer)

    await _sleep(interval_seconds)
    if await _post_cancelled_if_requested(entry, 8, randomizer):
        return

    await _post_event(
        entry,
        sequence=8,
        event_type="completed",
        status_value="succeeded",
        message="Mock ML completed training.",
        progress={
            **_build_progress(
                percent=100,
                epoch=7,
                total_epochs=7,
                randomizer=randomizer,
            ),
            "validationAccuracy": metrics["accuracy"],
        },
        result={
            "producedModelName": entry.output.produced_model_name,
            "primaryArtifactRelativePath": f"artifacts/{MODEL_ARTIFACT_FILE_NAME}",
            "reportStatus": "ok",
            "reportRelativePath": REPORT_FILE_NAME,
            "metricsSummary": {
                "accuracy": metrics["accuracy"],
                "macroF1": metrics["macroF1"],
            },
        },
    )
    _terminal_run_statuses[entry.run_name] = "succeeded"


async def _post_cancelled_if_requested(
    entry: StartTrainingApiEntry,
    sequence: int,
    randomizer: random.Random,
) -> bool:
    if entry.run_name not in _cancel_requested_run_names:
        return False

    _cancel_requested_run_names.discard(entry.run_name)
    await _post_event(
        entry,
        sequence=sequence,
        event_type="cancelled",
        status_value="cancelled",
        message="Mock ML cancelled training.",
        progress=_build_progress(
            percent=100,
            epoch=max(0, sequence - 1),
            total_epochs=7,
            randomizer=randomizer,
        ),
    )
    _terminal_run_statuses[entry.run_name] = "cancelled"
    return True


def _ensure_runtime_directories(entry: StartTrainingApiEntry) -> None:
    for directory_path in (
        entry.output.run_directory_path,
        entry.output.reports_directory_path,
        entry.output.working_directory_path,
        entry.output.produced_model_artifacts_directory_path,
    ):
        Path(directory_path).mkdir(parents=True, exist_ok=True)

    run_log_path = Path(entry.output.run_directory_path) / "mock-training.log"
    run_log_path.write_text(
        (
            f"Mock training run: {entry.run_name}\n"
            f"Base model: {entry.base_model.name}\n"
            f"Dataset: {entry.dataset.name}\n"
        ),
        encoding="utf-8",
    )


def _write_success_artifacts(
    entry: StartTrainingApiEntry,
    randomizer: random.Random,
) -> dict[str, float]:
    accuracy = round(randomizer.uniform(0.92, 0.98), 4)
    macro_f1 = round(max(0.0, accuracy - randomizer.uniform(0.005, 0.025)), 4)
    artifact_path = (
        Path(entry.output.produced_model_artifacts_directory_path)
        / MODEL_ARTIFACT_FILE_NAME
    )
    artifact_path.write_text(
        json.dumps(
            {
                "format": "mock-model",
                "runName": entry.run_name,
                "baseModelName": entry.base_model.name,
                "processedDatasetName": entry.dataset.name,
                "createdAtUtc": datetime.now(UTC).isoformat(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    report_path = Path(entry.output.reports_directory_path) / REPORT_FILE_NAME
    report_path.write_text(
        json.dumps(
            {
                "runName": entry.run_name,
                "status": "succeeded",
                "metricsSummary": {
                    "accuracy": accuracy,
                    "macroF1": macro_f1,
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return {"accuracy": accuracy, "macroF1": macro_f1}


async def _post_event(
    entry: StartTrainingApiEntry,
    sequence: int,
    event_type: str,
    status_value: str,
    message: str,
    progress: dict[str, float | int],
    result: dict[str, object] | None = None,
) -> None:
    payload = {
        "sequence": sequence,
        "eventType": event_type,
        "status": status_value,
        "occurredAtUtc": datetime.now(UTC).isoformat(),
        "message": message,
        "progress": progress,
        "result": result,
        "warnings": [],
    }

    max_attempts = _get_callback_max_attempts()
    retry_delay_seconds = _get_callback_retry_delay_seconds()

    async with httpx.AsyncClient(timeout=_get_callback_timeout_seconds()) as client:
        for attempt in range(1, max_attempts + 1):
            try:
                response = await client.post(_events_url(entry), json=payload)
                if response.status_code < 300:
                    return

                if response.status_code not in {409, 500, 502, 503, 504}:
                    return
            except httpx.HTTPError:
                pass

            if attempt < max_attempts:
                await _sleep(retry_delay_seconds)


def _events_url(entry: StartTrainingApiEntry) -> str:
    base_url = os.getenv(BACKEND_BASE_URL_ENV, DEFAULT_BACKEND_BASE_URL)
    return urljoin(f"{base_url.rstrip('/')}/", entry.callbacks.events_path.lstrip("/"))


def _build_progress(
    percent: int,
    epoch: int,
    total_epochs: int,
    randomizer: random.Random,
) -> dict[str, float | int]:
    normalized_epoch = max(epoch, 1)
    return {
        "percent": percent,
        "epoch": epoch,
        "totalEpochs": total_epochs,
        "trainLoss": round(0.9 / normalized_epoch, 4),
        "validationLoss": round(1.05 / normalized_epoch, 4),
        "trainAccuracy": round(randomizer.uniform(0.84, 0.98), 4),
        "validationAccuracy": round(randomizer.uniform(0.80, 0.96), 4),
    }


def _stable_seed(run_name: str, configured_seed: int) -> int:
    digest = hashlib.sha256(run_name.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) + configured_seed


def _get_interval_seconds() -> float:
    raw_value = os.getenv(INTERVAL_SECONDS_ENV)
    if raw_value is None:
        return DEFAULT_INTERVAL_SECONDS

    try:
        return max(0.0, float(raw_value))
    except ValueError:
        return DEFAULT_INTERVAL_SECONDS


def _get_callback_timeout_seconds() -> float:
    raw_value = os.getenv(CALLBACK_TIMEOUT_SECONDS_ENV)
    if raw_value is None:
        return DEFAULT_CALLBACK_TIMEOUT_SECONDS

    try:
        return max(1.0, float(raw_value))
    except ValueError:
        return DEFAULT_CALLBACK_TIMEOUT_SECONDS


def _get_callback_max_attempts() -> int:
    raw_value = os.getenv(CALLBACK_MAX_ATTEMPTS_ENV)
    if raw_value is None:
        return DEFAULT_CALLBACK_MAX_ATTEMPTS

    try:
        return max(1, int(raw_value))
    except ValueError:
        return DEFAULT_CALLBACK_MAX_ATTEMPTS


def _get_callback_retry_delay_seconds() -> float:
    raw_value = os.getenv(CALLBACK_RETRY_DELAY_SECONDS_ENV)
    if raw_value is None:
        return DEFAULT_CALLBACK_RETRY_DELAY_SECONDS

    try:
        return max(0.0, float(raw_value))
    except ValueError:
        return DEFAULT_CALLBACK_RETRY_DELAY_SECONDS


async def _sleep(interval_seconds: float) -> None:
    if interval_seconds > 0:
        await asyncio.sleep(interval_seconds)
