from collections.abc import Iterable

from torch import nn

from application.features.trainings.errors.training_run_errors import (
    TrainingRunValidationError,
)
from infrastructure.training.profiles.training_profile import TrainingProfile


class FineTuningPolicyFactory:
    def apply(
        self,
        model: nn.Module,
        profile: TrainingProfile,
    ) -> Iterable[nn.Parameter]:
        if profile.fine_tuning_policy == "all":
            for parameter in model.parameters():
                parameter.requires_grad = True
            return [parameter for parameter in model.parameters()]

        if profile.fine_tuning_policy == "head-only":
            for parameter in model.parameters():
                parameter.requires_grad = False
            if not hasattr(model, "fc"):
                raise TrainingRunValidationError(
                    "unsupported_fine_tuning_policy",
                    "Model nie ma głowicy fc wymaganej przez profil.",
                )
            for parameter in model.fc.parameters():
                parameter.requires_grad = True
            return [parameter for parameter in model.fc.parameters()]

        raise TrainingRunValidationError(
            "unsupported_fine_tuning_policy",
            "Polityka fine-tuningu nie jest obsługiwana.",
        )
