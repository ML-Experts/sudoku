import unittest

from init_bootstrap.bootstrap_declaration import parse_bootstrap_declaration
from init_bootstrap.exceptions import BootstrapConfigurationError
from init_bootstrap.manifest_builder import build_manifest


class ManifestBuilderTests(unittest.TestCase):
    def test_build_manifest_should_create_cnn_bootstrap_manifest(self) -> None:
        declaration = parse_bootstrap_declaration(
            {
                "family": "cnn",
                "type": "custom-cnn-v1",
                "name": "cnn-baseline",
                "displayName": "CNN baseline",
            }
        )

        manifest = build_manifest(declaration)

        self.assertEqual(manifest["name"], "cnn-baseline")
        self.assertEqual(manifest["sourceType"], "bootstrap")
        self.assertIsNone(manifest["sourceRunName"])
        self.assertEqual(manifest["architecture"]["inputChannels"], 1)
        self.assertFalse(manifest["capabilities"]["canUseForInference"])

    def test_build_manifest_should_create_resnet_manifest(self) -> None:
        declaration = parse_bootstrap_declaration(
            {
                "family": "resnet",
                "type": "resnet18",
                "displayName": "ResNet18 ImageNet bootstrap",
            }
        )

        manifest = build_manifest(declaration)

        self.assertEqual(manifest["name"], "resnet18-imagenet-bootstrap")
        self.assertEqual(manifest["architecture"]["library"], "torchvision")
        self.assertEqual(manifest["architecture"]["inputHeight"], 224)

    def test_build_manifest_should_create_larger_resnet_manifest(self) -> None:
        declaration = parse_bootstrap_declaration(
            {
                "family": "resnet",
                "type": "resnet152",
                "displayName": "ResNet152 ImageNet bootstrap",
            }
        )

        manifest = build_manifest(declaration)

        self.assertEqual(manifest["architecture"]["type"], "resnet152")
        self.assertEqual(manifest["architecture"]["variant"], "resnet152")
        self.assertEqual(
            manifest["architecture"]["pretrainedSource"],
            "ResNet152_Weights.DEFAULT",
        )

    def test_build_manifest_should_create_wide_resnet_manifest(self) -> None:
        declaration = parse_bootstrap_declaration(
            {
                "family": "resnet",
                "type": "wide_resnet101_2",
                "displayName": "Wide ResNet101 2 bootstrap",
            }
        )

        manifest = build_manifest(declaration)

        self.assertEqual(
            manifest["architecture"]["type"],
            "wide_resnet101_2",
        )
        self.assertEqual(
            manifest["architecture"]["pretrainedSource"],
            "Wide_ResNet101_2_Weights.DEFAULT",
        )

    def test_parse_declaration_should_reject_technical_overrides(self) -> None:
        with self.assertRaises(BootstrapConfigurationError):
            parse_bootstrap_declaration(
                {
                    "family": "cnn",
                    "type": "custom-cnn-v1",
                    "inputChannels": 3,
                }
            )


if __name__ == "__main__":
    unittest.main()

