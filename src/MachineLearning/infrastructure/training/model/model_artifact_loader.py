from pathlib import Path

import torch
from torch import nn

from application.features.trainings.errors.training_run_errors import (
    TrainingRunValidationError,
)
from models.model_manifest import ModelManifest


class ModelArtifactLoader:
    def load(
        self,
        model: nn.Module,
        artifact_path: str,
        manifest: ModelManifest,
        device: torch.device,
    ) -> None:
        if manifest.artifacts.format != "pytorch-state-dict":
            raise TrainingRunValidationError(
                "unsupported_model_artifact_format",
                "Obsługiwany jest wyłącznie format pytorch-state-dict.",
            )

        try:
            checkpoint = torch.load(Path(artifact_path), map_location=device)
        except Exception as error:
            raise TrainingRunValidationError(
                "base_model_artifact_invalid",
                "Nie udało się odczytać artefaktu modelu bazowego.",
            ) from error

        state_dict = checkpoint
        if isinstance(checkpoint, dict) and "state_dict" in checkpoint:
            state_dict = checkpoint["state_dict"]
        if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
            state_dict = checkpoint["model_state_dict"]

        try:
            model.load_state_dict(state_dict)
        except Exception as error:
            raise TrainingRunValidationError(
                "base_model_artifact_invalid",
                "Artefakt modelu bazowego nie pasuje do manifestu.",
            ) from error
