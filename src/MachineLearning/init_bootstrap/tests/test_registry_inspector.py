import tempfile
import unittest
from pathlib import Path

from init_bootstrap.bootstrap_declaration import parse_bootstrap_declaration
from init_bootstrap.manifest_builder import build_manifest
from init_bootstrap.manifest_io import write_manifest
from init_bootstrap.registry_inspector import inspect_registry_entry


class RegistryInspectorTests(unittest.TestCase):
    def test_inspect_registry_entry_should_return_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest = self._build_manifest()

            inspection = inspect_registry_entry(Path(temp_dir), manifest)

            self.assertTrue(inspection.is_missing)

    def test_inspect_registry_entry_should_return_complete(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            registry_path = Path(temp_dir)
            manifest = self._build_manifest()
            model_path = registry_path / manifest["name"]
            artifact_path = (
                model_path
                / manifest["artifacts"]["primaryArtifactRelativePath"]
            )
            artifact_path.parent.mkdir(parents=True)
            artifact_path.write_bytes(b"model")
            write_manifest(model_path / "model.json", manifest)

            inspection = inspect_registry_entry(registry_path, manifest)

            self.assertTrue(inspection.is_complete)

    def test_inspect_registry_entry_should_return_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            registry_path = Path(temp_dir)
            manifest = self._build_manifest()
            (registry_path / manifest["name"]).mkdir()

            inspection = inspect_registry_entry(registry_path, manifest)

            self.assertTrue(inspection.is_incomplete)
            self.assertIn("model.json", inspection.reasons)

    def _build_manifest(self) -> dict:
        declaration = parse_bootstrap_declaration(
            {
                "family": "cnn",
                "type": "custom-cnn-v1",
                "name": "cnn-baseline",
            }
        )
        return build_manifest(declaration)


if __name__ == "__main__":
    unittest.main()

