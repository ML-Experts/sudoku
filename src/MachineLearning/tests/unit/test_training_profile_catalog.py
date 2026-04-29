import unittest

from infrastructure.training.profiles.training_profile_catalog import (
    TrainingProfileCatalog,
)
from models.model_manifest import ModelArchitecture, ModelArtifacts, ModelManifest


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
    )


class TrainingProfileCatalogTests(unittest.TestCase):
    def test_get_should_apply_max_epochs_override(self) -> None:
        catalog = TrainingProfileCatalog(max_epochs_override=1)

        profile = catalog.get("cnn-default-v1", _manifest())

        self.assertEqual(profile.epochs, 1)

    def test_get_should_reject_architecture_mismatch(self) -> None:
        catalog = TrainingProfileCatalog()

        with self.assertRaises(Exception):
            catalog.get("cnn-default-v1", _manifest(family="resnet"))


if __name__ == "__main__":
    unittest.main()
