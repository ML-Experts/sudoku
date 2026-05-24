from application.features.trainings.dto.training_run_context_dto import (
    TrainingParametersDto,
)
from application.features.trainings.errors.training_run_errors import (
    TrainingRunValidationError,
)
from infrastructure.training.profiles.training_profile import TrainingProfile
from models.model_manifest import ModelManifest


class TrainingProfileCatalog:
    def __init__(self, max_epochs_override: int | None = None) -> None:
        self._max_epochs_override = max_epochs_override
        self._profiles = {
            "cnn-default-v1": TrainingProfile(
                name="cnn-default-v1",
                architecture_family="cnn",
                epochs=40,
                batch_size=64,
                learning_rate=0.001,
                optimizer="adam",
                fine_tuning_policy="all",
                early_stopping_patience=6,
                early_stopping_min_delta=0.001,
                warmup_epochs=0,
                lr_scheduler_patience=3,
                lr_scheduler_factor=0.5,
            ),
            "resnet18-finetune-v1": TrainingProfile(
                name="resnet18-finetune-v1",
                architecture_family="resnet",
                epochs=10,
                batch_size=32,
                learning_rate=0.0001,
                optimizer="adam",
                fine_tuning_policy="head-only",
                early_stopping_patience=4,
                early_stopping_min_delta=0.001,
                warmup_epochs=0,
                lr_scheduler_patience=2,
                lr_scheduler_factor=0.5,
            ),
        }

    def get(
        self,
        profile_name: str,
        manifest: ModelManifest,
    ) -> TrainingProfile:
        profile = self._profiles.get(profile_name)
        if profile is None:
            raise TrainingRunValidationError(
                "unsupported_training_profile",
                "Profil treningowy nie jest obsługiwany.",
            )
        if profile.architecture_family != manifest.architecture.family:
            raise TrainingRunValidationError(
                "training_profile_architecture_mismatch",
                "Profil treningowy nie pasuje do rodziny architektury modelu.",
            )
        return self._apply_max_epochs_override(profile)

    def create_effective_profile(
        self,
        manifest: ModelManifest,
        training_parameters: TrainingParametersDto,
        profile_name: str | None = None,
    ) -> TrainingProfile:
        profile = TrainingProfile(
            name=profile_name or f"{manifest.architecture.family}-runtime",
            architecture_family=manifest.architecture.family,
            epochs=training_parameters.epochs,
            batch_size=training_parameters.batch_size,
            learning_rate=training_parameters.learning_rate,
            optimizer="adam",
            fine_tuning_policy=training_parameters.fine_tuning_policy,
            early_stopping_patience=training_parameters.early_stopping_patience,
            early_stopping_min_delta=training_parameters.early_stopping_min_delta,
            warmup_epochs=training_parameters.warmup_epochs,
            lr_scheduler_patience=training_parameters.lr_scheduler_patience,
            lr_scheduler_factor=training_parameters.lr_scheduler_factor,
        )
        return self._apply_max_epochs_override(profile)

    def _apply_max_epochs_override(
        self,
        profile: TrainingProfile,
    ) -> TrainingProfile:
        if self._max_epochs_override is None or self._max_epochs_override <= 0:
            return profile

        return TrainingProfile(
            name=profile.name,
            architecture_family=profile.architecture_family,
            epochs=min(profile.epochs, self._max_epochs_override),
            batch_size=profile.batch_size,
            learning_rate=profile.learning_rate,
            optimizer=profile.optimizer,
            fine_tuning_policy=profile.fine_tuning_policy,
            early_stopping_patience=profile.early_stopping_patience,
            early_stopping_min_delta=profile.early_stopping_min_delta,
            warmup_epochs=profile.warmup_epochs,
            lr_scheduler_patience=profile.lr_scheduler_patience,
            lr_scheduler_factor=profile.lr_scheduler_factor,
        )
