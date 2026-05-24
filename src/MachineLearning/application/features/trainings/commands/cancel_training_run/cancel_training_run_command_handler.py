from application.features.trainings.commands.cancel_training_run.cancel_training_run_command import (
    CancelTrainingRunCommand,
)
from application.features.trainings.commands.cancel_training_run.cancel_training_run_command_result_dto import (
    CancelTrainingRunCommandResultDto,
)
from application.features.trainings.ports.training_ports import CancellationRegistry


class CancelTrainingRunCommandHandler:
    def __init__(self, cancellation_registry: CancellationRegistry) -> None:
        self._cancellation_registry = cancellation_registry

    def handle(
        self, command: CancelTrainingRunCommand
    ) -> CancelTrainingRunCommandResultDto:
        result = self._cancellation_registry.request_cancel(command.run_name)
        return CancelTrainingRunCommandResultDto(
            run_name=command.run_name,
            status=result.status,
            request_disposition=result.request_disposition,
            cancellation_requested_at_utc=result.cancellation_requested_at_utc,
        )
