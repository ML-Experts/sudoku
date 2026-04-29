from torch import nn
from torchvision import models as torchvision_models

from application.features.trainings.errors.training_run_errors import (
    TrainingRunValidationError,
)
from infrastructure.training.model.custom_digit_cnn_v1 import CustomDigitCnnV1
from models.model_manifest import ModelManifest


class ModelFactory:
    def build(self, manifest: ModelManifest) -> nn.Module:
        architecture_type = manifest.architecture.type
        if architecture_type == "custom-cnn-v1":
            return CustomDigitCnnV1(
                num_classes=manifest.architecture.num_classes,
                input_channels=manifest.architecture.input_channels,
            )
        if architecture_type == "resnet18":
            model = torchvision_models.resnet18(weights=None)
            model.fc = nn.Linear(
                model.fc.in_features,
                manifest.architecture.num_classes,
            )
            return model
        if architecture_type == "resnet50":
            model = torchvision_models.resnet50(weights=None)
            model.fc = nn.Linear(
                model.fc.in_features,
                manifest.architecture.num_classes,
            )
            return model

        raise TrainingRunValidationError(
            "unsupported_model_architecture",
            "Typ architektury modelu nie jest obsługiwany.",
        )
