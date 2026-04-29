import tempfile
import unittest
from pathlib import Path

from init_bootstrap.bootstrap_declaration import parse_bootstrap_declaration
from init_bootstrap.exceptions import BootstrapRegistryEntryIncompleteError
from init_bootstrap.manifest_builder import build_manifest
from init_bootstrap.registry_inspector import inspect_registry_entry
from init_bootstrap.registry_writer import write_registry_entry


class RegistryWriterIdempotencyTests(unittest.TestCase):
    def test_write_registry_entry_should_create_entry(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            registry_path = Path(temp_dir)
            manifest = self._build_manifest()

            write_registry_entry(
                registry_path,
                manifest,
                model=object(),
                overwrite=False,
                artifact_serializer=self._write_fake_artifact,
            )

            inspection = inspect_registry_entry(registry_path, manifest)
            self.assertTrue(inspection.is_complete)

    def test_incomplete_entry_should_be_rejected_without_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            registry_path = Path(temp_dir)
            manifest = self._build_manifest()
            (registry_path / manifest["name"]).mkdir()
            inspection = inspect_registry_entry(registry_path, manifest)

            with self.assertRaises(BootstrapRegistryEntryIncompleteError):
                if inspection.is_incomplete:
                    raise BootstrapRegistryEntryIncompleteError(
                        manifest["name"], inspection.reasons
                    )

    def test_write_registry_entry_should_overwrite_when_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            registry_path = Path(temp_dir)
            manifest = self._build_manifest()
            model_path = registry_path / manifest["name"]
            model_path.mkdir()

            write_registry_entry(
                registry_path,
                manifest,
                model=object(),
                overwrite=True,
                artifact_serializer=self._write_fake_artifact,
            )

            self.assertTrue((model_path / "model.json").is_file())

    def _build_manifest(self) -> dict:
        declaration = parse_bootstrap_declaration(
            {
                "family": "cnn",
                "type": "custom-cnn-v1",
                "name": "cnn-baseline",
            }
        )
        return build_manifest(declaration)

    def _write_fake_artifact(self, model: object, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"fake-model")


if __name__ == "__main__":
    unittest.main()

