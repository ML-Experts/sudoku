import unittest

from init_bootstrap.exceptions import BootstrapConfigurationError
from init_bootstrap.settings import load_bootstrap_settings


class SettingsTests(unittest.TestCase):
    def test_load_bootstrap_settings_should_parse_values(self) -> None:
        settings = load_bootstrap_settings(
            {
                "ML_MODELS_REGISTRY_DIRECTORY_PATH": "/tmp/registry",
                "ML_ACTIVE_MODEL_DIRECTORY_PATH": "/tmp/active",
                "ML_BOOTSTRAP_MODELS_JSON": (
                    '[{"family":"cnn","type":"custom-cnn-v1",'
                    '"name":"cnn-baseline","displayName":"CNN baseline"}]'
                ),
                "ML_BOOTSTRAP_OVERWRITE_EXISTING": "false",
                "ML_BOOTSTRAP_SET_ACTIVE_IF_MISSING": "true",
                "ML_BOOTSTRAP_DEFAULT_ACTIVE_MODEL": "cnn-baseline",
            }
        )

        self.assertEqual(settings.registry_directory_path.as_posix(), "/tmp/registry")
        self.assertFalse(settings.overwrite_existing)
        self.assertTrue(settings.set_active_if_missing)
        self.assertEqual(settings.declarations[0].name, "cnn-baseline")

    def test_load_bootstrap_settings_should_accept_deploy_aliases(self) -> None:
        settings = load_bootstrap_settings(
            {
                "ML_MODELS_REGISTRY_DIR": "/tmp/registry",
                "ML_MODELS_ACTIVE_DIR": "/tmp/active",
                "ML_BOOTSTRAP_MODELS_JSON": (
                    '[{"family":"resnet","type":"resnet18",'
                    '"displayName":"ResNet18 ImageNet bootstrap"}]'
                ),
                "ML_BOOTSTRAP_OVERWRITE_EXISTING": "0",
                "ML_BOOTSTRAP_SET_ACTIVE_IF_MISSING": "1",
            }
        )

        self.assertEqual(
            settings.declarations[0].name,
            "resnet18-imagenet-bootstrap",
        )

    def test_load_bootstrap_settings_should_reject_relative_paths(self) -> None:
        with self.assertRaises(BootstrapConfigurationError) as raised_error:
            load_bootstrap_settings(
                {
                    "ML_MODELS_REGISTRY_DIRECTORY_PATH": "./registry",
                    "ML_ACTIVE_MODEL_DIRECTORY_PATH": "/tmp/active",
                    "ML_BOOTSTRAP_MODELS_JSON": (
                        '[{"family":"cnn","type":"custom-cnn-v1"}]'
                    ),
                    "ML_BOOTSTRAP_OVERWRITE_EXISTING": "false",
                    "ML_BOOTSTRAP_SET_ACTIVE_IF_MISSING": "false",
                }
            )

        self.assertEqual(
            raised_error.exception.error_type,
            "bootstrap_configuration_invalid",
        )


if __name__ == "__main__":
    unittest.main()

