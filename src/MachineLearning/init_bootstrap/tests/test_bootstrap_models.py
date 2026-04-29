import tempfile
import unittest
from pathlib import Path
from typing import Any

from init_bootstrap.bootstrap_declaration import BootstrapModelDeclaration
from init_bootstrap.bootstrap_models import BootstrapModelsApplication
from init_bootstrap.settings import BootstrapSettings


class BootstrapModelsApplicationTests(unittest.TestCase):
    def test_run_should_create_entry_and_skip_second_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir)
            settings = self._build_settings(root_path)
            application = BootstrapModelsApplication(
                model_builder=lambda manifest: object(),
                artifact_serializer=self._write_fake_artifact,
            )

            first_result = application.run(settings)
            second_result = application.run(settings)

            self.assertEqual(first_result.model_results[0].status, "created")
            self.assertEqual(second_result.model_results[0].status, "skipped")
            self.assertEqual(
                second_result.model_results[0].reason,
                "entry_complete",
            )

    def test_run_should_report_incomplete_entry_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir)
            settings = self._build_settings(root_path)
            (settings.registry_directory_path / "cnn-baseline").mkdir(
                parents=True
            )
            application = BootstrapModelsApplication(
                model_builder=lambda manifest: object(),
                artifact_serializer=self._write_fake_artifact,
            )

            result = application.run(settings)

            self.assertEqual(result.model_results[0].status, "failed")
            self.assertEqual(
                result.model_results[0].error_type,
                "bootstrap_registry_entry_incomplete",
            )

    def _build_settings(self, root_path: Path) -> BootstrapSettings:
        declaration = BootstrapModelDeclaration(
            family="cnn",
            model_type="custom-cnn-v1",
            name="cnn-baseline",
            display_name="CNN baseline",
        )
        return BootstrapSettings(
            registry_directory_path=root_path / "registry",
            active_model_directory_path=root_path / "active",
            declarations=[declaration],
            overwrite_existing=False,
            set_active_if_missing=False,
            default_active_model=None,
        )

    def _write_fake_artifact(self, model: Any, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"fake")


if __name__ == "__main__":
    unittest.main()

