from application.features.trainings.errors.training_run_errors import (
    TrainingRunValidationError,
)
from infrastructure.training.data.input_transforms import (
    CnnInputTransform,
    InputTransform,
    ResNetInputTransform,
)
from models.model_manifest import ModelManifest


class InputTransformFactory:
    def build(
        self,
        manifest: ModelManifest,
        augmentation_profile_name: str,
    ) -> InputTransform:
        if augmentation_profile_name != "digits-light-v1":
            raise TrainingRunValidationError(
                "unsupported_augmentation_profile",
                "Profil augmentacji nie jest obsługiwany.",
            )

        if manifest.architecture.family == "cnn":
            return CnnInputTransform()
        if manifest.architecture.family == "resnet":
            return ResNetInputTransform(
                height=manifest.architecture.input_height,
                width=manifest.architecture.input_width,
            )

        raise TrainingRunValidationError(
            "unsupported_model_architecture",
            "Rodzina architektury modelu nie jest obsługiwana.",
        )
