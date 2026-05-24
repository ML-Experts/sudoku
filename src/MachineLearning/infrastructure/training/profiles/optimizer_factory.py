from collections.abc import Iterable

import torch
from torch import nn

from application.features.trainings.errors.training_run_errors import (
    TrainingRunValidationError,
)
from infrastructure.training.profiles.training_profile import TrainingProfile


class OptimizerFactory:
    def build(
        self,
        profile: TrainingProfile,
        parameters: Iterable[nn.Parameter],
    ) -> torch.optim.Optimizer:
        if profile.optimizer == "adam":
            return torch.optim.Adam(
                list(parameters),
                lr=profile.learning_rate,
            )

        raise TrainingRunValidationError(
            "unsupported_optimizer",
            "Optimizer profilu treningowego nie jest obsługiwany.",
        )
