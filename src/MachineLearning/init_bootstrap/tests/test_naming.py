import unittest

from init_bootstrap.exceptions import BootstrapConfigurationError
from init_bootstrap.naming import (
    ensure_unique_model_names,
    generate_model_name,
    slug_model_name,
    validate_model_name,
)


class NamingTests(unittest.TestCase):
    def test_slug_model_name_should_normalize_text(self) -> None:
        self.assertEqual(
            slug_model_name("ResNet18 ImageNet bootstrap"),
            "resnet18-imagenet-bootstrap",
        )

    def test_generate_model_name_should_prefer_explicit_name(self) -> None:
        model_name = generate_model_name(
            family="resnet",
            model_type="resnet18",
            display_name="Other name",
            explicit_name="resnet-seed",
        )

        self.assertEqual(model_name, "resnet-seed")

    def test_validate_model_name_should_reject_invalid_name(self) -> None:
        with self.assertRaises(BootstrapConfigurationError):
            validate_model_name("-bad-name")

    def test_ensure_unique_model_names_should_reject_duplicates(self) -> None:
        with self.assertRaises(BootstrapConfigurationError) as raised_error:
            ensure_unique_model_names(["cnn", "resnet", "cnn"])

        self.assertEqual(
            raised_error.exception.error_type,
            "bootstrap_model_name_collision",
        )


if __name__ == "__main__":
    unittest.main()

