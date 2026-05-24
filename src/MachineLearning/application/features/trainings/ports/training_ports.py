from datetime import datetime
from typing import Awaitable, Callable, Protocol

from application.features.trainings.dto.training_run_context_dto import (
    TrainingRunContextDto,
)
from application.features.trainings.dto.training_run_event_dto import (
    TrainingRunEventDto,
)
from models.model_manifest import ModelManifest


class CancellationToken(Protocol):
    def throw_if_cancelled(self) -> None: ...


class TrainingRunner(Protocol):
    async def start(
        self,
        context: TrainingRunContextDto,
        cancellation_token: CancellationToken,
    ) -> None: ...


class TrainingEventPublisher(Protocol):
    async def publish(
        self,
        event: TrainingRunEventDto,
        *,
        terminal: bool = False,
    ) -> None: ...


class ModelManifestReader(Protocol):
    def read(self, manifest_path: str) -> ModelManifest: ...


class FilesystemPathValidator(Protocol):
    def ensure_file_exists(self, path: str, error_type: str) -> None: ...

    def ensure_output_paths_are_allowed(self, paths: tuple[str, ...]) -> None: ...


class ActiveTrainingRunGuard(Protocol):
    def ensure_no_active_run(self) -> None: ...

    def reserve(self, run_name: str) -> CancellationToken: ...

    def release(self, run_name: str) -> None: ...


class CancellationRegistry(ActiveTrainingRunGuard, Protocol):
    def request_cancel(self, run_name: str) -> object: ...


class UtcClock(Protocol):
    def now(self) -> datetime: ...


TaskScheduler = Callable[[Callable[..., Awaitable[None]], object, object], None]
