import json
import tempfile
import unittest
from pathlib import Path

from init_bootstrap.active_model_writer import ensure_active_model_if_missing


class ActiveModelWriterTests(unittest.TestCase):
    def test_should_create_active_model_pointer_for_sudoku_inference_model(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir)
            registry_path = root_path / "registry"
            active_path = root_path / "active"
            self._write_manifest(
                registry_path / "cnn-baseline" / "model.json",
                can_use_for_inference=True,
                num_classes=9,
            )

            result = ensure_active_model_if_missing(
                active_model_directory_path=active_path,
                registry_directory_path=registry_path,
                default_active_model="cnn-baseline",
                set_active_if_missing=True,
            )

            self.assertEqual(result.status, "created")
            pointer = json.loads(
                (active_path / "inference.json").read_text(encoding="utf-8")
            )
            self.assertEqual(pointer["modelName"], "cnn-baseline")

    def test_should_skip_when_active_pointer_exists(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir)
            active_path = root_path / "active"
            active_path.mkdir()
            (active_path / "inference.json").write_text("{}", encoding="utf-8")

            result = ensure_active_model_if_missing(
                active_model_directory_path=active_path,
                registry_directory_path=root_path / "registry",
                default_active_model="cnn-baseline",
                set_active_if_missing=True,
            )

            self.assertEqual(result.reason, "active_model_already_set")

    def test_should_skip_non_inference_model(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir)
            registry_path = root_path / "registry"
            active_path = root_path / "active"
            self._write_manifest(
                registry_path / "cnn-baseline" / "model.json",
                can_use_for_inference=False,
                num_classes=9,
            )

            result = ensure_active_model_if_missing(
                active_model_directory_path=active_path,
                registry_directory_path=registry_path,
                default_active_model="cnn-baseline",
                set_active_if_missing=True,
            )

            self.assertEqual(result.reason, "model_not_inference_capable")

    def test_should_skip_10_class_model_even_when_flagged_for_inference(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir)
            registry_path = root_path / "registry"
            active_path = root_path / "active"
            self._write_manifest(
                registry_path / "cnn-baseline" / "model.json",
                can_use_for_inference=True,
                num_classes=10,
            )

            result = ensure_active_model_if_missing(
                active_model_directory_path=active_path,
                registry_directory_path=registry_path,
                default_active_model="cnn-baseline",
                set_active_if_missing=True,
            )

            self.assertEqual(result.reason, "model_not_inference_capable")

    def _write_manifest(
        self, path: Path, *, can_use_for_inference: bool, num_classes: int
    ) -> None:
        path.parent.mkdir(parents=True)
        path.write_text(
            json.dumps(
                {
                    "name": path.parent.name,
                    "architecture": {"numClasses": num_classes},
                    "capabilities": {
                        "canUseForInference": can_use_for_inference
                    },
                }
            ),
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()

