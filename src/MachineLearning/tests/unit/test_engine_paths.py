import tempfile
import unittest
from pathlib import Path

from infrastructure.vision.engine.paths import find_runtime_root


class EnginePathsTests(unittest.TestCase):
    def test_find_runtime_root_should_resolve_release_layout_without_repo_markers(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            runtime_root = Path(temp_directory) / "ml"
            engine_dir = runtime_root / "infrastructure" / "vision" / "engine"

            for relative_path in (
                "api",
                "application",
                "infrastructure",
                "models",
            ):
                (runtime_root / relative_path).mkdir(parents=True, exist_ok=True)

            engine_dir.mkdir(parents=True, exist_ok=True)
            (runtime_root / "requirements.txt").write_text("", encoding="utf-8")

            resolved_root = find_runtime_root(engine_dir)

            self.assertEqual(resolved_root, runtime_root)


if __name__ == "__main__":
    unittest.main()
