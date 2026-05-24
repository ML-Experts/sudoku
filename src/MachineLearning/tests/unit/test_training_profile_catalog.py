import unittest

from application.features.trainings.dto.training_run_context_dto import (
    TrainingParametersDto,
)
from infrastructure.training.profiles.training_profile_catalog import (
    TrainingProfileCatalog,
)
from models.model_manifest import (
    ModelArchitecture,
    ModelArtifacts,
    ModelCapabilities,
    ModelManifest,
)


def _manifest(family: str = "cnn") -> ModelManifest:
    return ModelManifest(
        framework="pytorch",
        architecture=ModelArchitecture(
            type="custom-cnn-v1" if family == "cnn" else "resnet18",
            family=family,
            num_classes=10,
            input_channels=1 if family == "cnn" else 3,
            input_height=28 if family == "cnn" else 224,
            input_width=28 if family == "cnn" else 224,
            input_profile="default-28x28-v1",
        ),
        artifacts=ModelArtifacts(
            primary_artifact_relative_path="artifacts/model.pt",
            format="pytorch-state-dict",
        ),
        capabilities=ModelCapabilities(
            can_start_training=True,
            can_use_for_inference=True,
        ),
    )


class TrainingProfileCatalogTests(unittest.TestCase):
    def test_get_should_return_cnn_profile_with_40_epochs_and_training_controls(
        self,
    ) -> None:
        catalog = TrainingProfileCatalog()

        profile = catalog.get("cnn-default-v1", _manifest())

        self.assertEqual(profile.epochs, 40)
        self.assertEqual(profile.early_stopping_patience, 6)
        self.assertEqual(profile.lr_scheduler_patience, 3)
        self.assertEqual(profile.lr_scheduler_factor, 0.5)

    def test_get_should_apply_max_epochs_override(self) -> None:
        catalog = TrainingProfileCatalog(max_epochs_override=1)

        profile = catalog.get("cnn-default-v1", _manifest())

        self.assertEqual(profile.epochs, 1)
        self.assertEqual(profile.early_stopping_patience, 6)

    def test_get_should_reject_architecture_mismatch(self) -> None:
        catalog = TrainingProfileCatalog()

        with self.assertRaises(Exception):
            catalog.get("cnn-default-v1", _manifest(family="resnet"))

    def test_create_effective_profile_should_use_runtime_parameters(self) -> None:
        catalog = TrainingProfileCatalog(max_epochs_override=3)

        profile = catalog.create_effective_profile(
            _manifest(),
            TrainingParametersDto(
                epochs=5,
                learning_rate=0.002,
                batch_size=16,
                early_stopping_patience=4,
                lr_scheduler_patience=2,
                lr_scheduler_factor=0.4,
                fine_tuning_policy="all",
            ),
            profile_name="runtime-cnn",
        )

        self.assertEqual(profile.name, "runtime-cnn")
        self.assertEqual(profile.architecture_family, "cnn")
        self.assertEqual(profile.epochs, 3)
        self.assertEqual(profile.learning_rate, 0.002)
        self.assertEqual(profile.batch_size, 16)
        self.assertEqual(profile.early_stopping_patience, 4)
        self.assertEqual(profile.lr_scheduler_patience, 2)
        self.assertEqual(profile.lr_scheduler_factor, 0.4)
        self.assertEqual(profile.fine_tuning_policy, "all")


if __name__ == "__main__":
    unittest.main()
