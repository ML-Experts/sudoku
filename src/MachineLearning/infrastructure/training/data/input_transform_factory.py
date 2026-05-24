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

        return self._build_for_architecture(manifest)

    def build_for_inference(
        self,
        manifest: ModelManifest,
        inference_profile_name: str,
    ) -> InputTransform:
        if inference_profile_name != "default-28x28-v1":
            raise TrainingRunValidationError(
                "unsupported_input_profile",
                "Profil wejściowy inferencji nie jest obsługiwany.",
            )

        if inference_profile_name != manifest.architecture.input_profile:
            raise TrainingRunValidationError(
                "input_profile_mismatch",
                "Profil inferencji nie pasuje do manifestu modelu.",
            )

        return self._build_for_architecture(manifest)

    def _build_for_architecture(self, manifest: ModelManifest) -> InputTransform:
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
