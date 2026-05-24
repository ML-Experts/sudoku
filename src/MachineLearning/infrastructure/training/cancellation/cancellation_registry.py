from dataclasses import dataclass
from datetime import datetime
from threading import Lock

from application.features.trainings.errors.training_run_errors import (
    TrainingRunConflictError,
)
from infrastructure.time.system_utc_clock import SystemUtcClock
from infrastructure.training.cancellation.cancellation_token import CancellationToken


@dataclass(frozen=True)
class CancellationRequestResult:
    status: str | None
    request_disposition: str
    cancellation_requested_at_utc: datetime | None


@dataclass
class _ActiveRun:
    run_name: str
    status: str
    token: CancellationToken
    cancellation_requested_at_utc: datetime | None = None
    finished: bool = False


class CancellationRegistry:
    def __init__(self) -> None:
        self._lock = Lock()
        self._active_run: _ActiveRun | None = None
        self._clock = SystemUtcClock()

    def ensure_no_active_run(self) -> None:
        with self._lock:
            if self._active_run is not None and not self._active_run.finished:
                raise TrainingRunConflictError(
                    "training_run_already_active",
                    "Serwis ML wykonuje już aktywny run i nie przyjmuje nowego żądania startu.",
                )

    def reserve(self, run_name: str) -> CancellationToken:
        with self._lock:
            if self._active_run is not None and not self._active_run.finished:
                raise TrainingRunConflictError(
                    "training_run_already_active",
                    "Serwis ML wykonuje już aktywny run i nie przyjmuje nowego żądania startu.",
                )
            token = CancellationToken()
            self._active_run = _ActiveRun(
                run_name=run_name,
                status="queued",
                token=token,
            )
            return token

    def mark_running(self, run_name: str) -> None:
        with self._lock:
            if self._matches_active(run_name):
                self._active_run.status = "running"

    def release(self, run_name: str) -> None:
        with self._lock:
            if self._matches_active(run_name):
                self._active_run = None

    def request_cancel(self, run_name: str) -> CancellationRequestResult:
        with self._lock:
            if self._active_run is None or self._active_run.run_name != run_name:
                return CancellationRequestResult(
                    status=None,
                    request_disposition="noopNoMatchingRun",
                    cancellation_requested_at_utc=None,
                )

            active_run = self._active_run
            if active_run.finished:
                return CancellationRequestResult(
                    status=active_run.status,
                    request_disposition="noopAlreadyFinished",
                    cancellation_requested_at_utc=(
                        active_run.cancellation_requested_at_utc
                    ),
                )

            if active_run.cancellation_requested_at_utc is not None:
                return CancellationRequestResult(
                    status="cancelling",
                    request_disposition="alreadyCancelling",
                    cancellation_requested_at_utc=(
                        active_run.cancellation_requested_at_utc
                    ),
                )

            requested_at = self._clock.now()
            active_run.cancellation_requested_at_utc = requested_at
            active_run.status = "cancelling"
            active_run.token.request_cancel()
            return CancellationRequestResult(
                status="cancelling",
                request_disposition="cancellationRequested",
                cancellation_requested_at_utc=requested_at,
            )

    def _matches_active(self, run_name: str) -> bool:
        return self._active_run is not None and self._active_run.run_name == run_name
