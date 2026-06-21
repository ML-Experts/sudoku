import json
import os
import struct
import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np
from fastapi.testclient import TestClient

from api.main import create_app


class DatasetsControllerTests(unittest.TestCase):
    def setUp(self) -> None:
        self._env_keys = (
            "ML_ENVIRONMENT",
            "ML_BOARDS_SUBDIRECTORY",
            "ML_DIGITS_SUBDIRECTORY",
            "ML_TEMP_DATASETS_DIRECTORY_PATH",
            "ML_DATASET_PREVIEWS_DIRECTORY_PATH",
            "ML_DATASET_PREPARATIONS_DIRECTORY_PATH",
            "ML_EXAMPLES_UPLOADS_DIR",
            "ML_MODELS_ACTIVE_DIR",
            "ML_MODELS_REGISTRY_DIR",
        )
        self._previous_env = {
            key: os.environ.get(key) for key in self._env_keys
        }

    def tearDown(self) -> None:
        for key, value in self._previous_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_post_prepare_should_write_npz_from_preparation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            root_path = Path(temp_directory)
            boards_path = root_path / "boards"
            digits_path = root_path / "digits"
            datasets_path = root_path / "datasets"
            previews_path = root_path / "previews"
            preparations_path = root_path / "preparations"
            examples_path = root_path / "examples"
            models_active_path = root_path / "models" / "active"
            models_registry_path = root_path / "models" / "registry"

            boards_path.mkdir(parents=True)
            digits_path.mkdir(parents=True)
            datasets_path.mkdir(parents=True)
            previews_path.mkdir(parents=True)
            preparations_path.mkdir(parents=True)
            examples_path.mkdir(parents=True)
            models_active_path.mkdir(parents=True)
            models_registry_path.mkdir(parents=True)
            _write_digit_preparation(
                preparations_path=preparations_path,
                preparation_name="prep-1",
                source_name="mnist_train",
            )

            os.environ["ML_ENVIRONMENT"] = "local"
            os.environ["ML_BOARDS_SUBDIRECTORY"] = str(boards_path)
            os.environ["ML_DIGITS_SUBDIRECTORY"] = str(digits_path)
            os.environ["ML_TEMP_DATASETS_DIRECTORY_PATH"] = str(datasets_path)
            os.environ["ML_DATASET_PREVIEWS_DIRECTORY_PATH"] = str(
                previews_path
            )
            os.environ["ML_DATASET_PREPARATIONS_DIRECTORY_PATH"] = str(
                preparations_path
            )
            os.environ["ML_EXAMPLES_UPLOADS_DIR"] = str(examples_path)
            os.environ["ML_MODELS_ACTIVE_DIR"] = str(models_active_path)
            os.environ["ML_MODELS_REGISTRY_DIR"] = str(models_registry_path)

            client = TestClient(create_app())
            payload = {
                "preparationName": "prep-1",
                "datasetName": "digits-v1",
                "splitPolicy": {
                    "mode": "ratio",
                    "groupBy": "sourceType",
                    "ratios": {
                        "train": 1.0,
                        "val": 0.0,
                        "test": 0.0,
                    },
                },
                "sources": [
                    {
                        "name": "mnist_train",
                        "type": "digit",
                        "splits": ["mix"],
                    }
                ],
            }

            response = client.post("/ml/datasets/prepare", json=payload)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["datasetName"], "digits-v1")
            self.assertEqual(response.json()["fileName"], "digits-v1.npz")
            self.assertEqual(
                response.json()["preprocessingProfile"],
                "default-28x28-v1",
            )
            self.assertEqual(
                response.json()["sampleCounts"],
                {"train": 2, "val": 0, "test": 0},
            )
            self.assertTrue((datasets_path / "digits-v1.npz").is_file())

    def test_post_preparations_should_write_digit_preparation_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            root_path = Path(temp_directory)
            boards_path = root_path / "boards"
            digits_path = root_path / "digits"
            datasets_path = root_path / "datasets"
            previews_path = root_path / "previews"
            preparations_path = root_path / "preparations"
            examples_path = root_path / "examples"
            models_active_path = root_path / "models" / "active"
            models_registry_path = root_path / "models" / "registry"

            boards_path.mkdir(parents=True)
            digits_path.mkdir(parents=True)
            datasets_path.mkdir(parents=True)
            previews_path.mkdir(parents=True)
            preparations_path.mkdir(parents=True)
            examples_path.mkdir(parents=True)
            models_active_path.mkdir(parents=True)
            models_registry_path.mkdir(parents=True)

            _write_idx_pair(
                digits_path / "mnist_train.idx3-ubyte",
                digits_path / "mnist_train.idx1-ubyte",
            )

            os.environ["ML_ENVIRONMENT"] = "local"
            os.environ["ML_BOARDS_SUBDIRECTORY"] = str(boards_path)
            os.environ["ML_DIGITS_SUBDIRECTORY"] = str(digits_path)
            os.environ["ML_TEMP_DATASETS_DIRECTORY_PATH"] = str(datasets_path)
            os.environ["ML_DATASET_PREVIEWS_DIRECTORY_PATH"] = str(
                previews_path
            )
            os.environ["ML_DATASET_PREPARATIONS_DIRECTORY_PATH"] = str(
                preparations_path
            )
            os.environ["ML_EXAMPLES_UPLOADS_DIR"] = str(examples_path)
            os.environ["ML_MODELS_ACTIVE_DIR"] = str(models_active_path)
            os.environ["ML_MODELS_REGISTRY_DIR"] = str(models_registry_path)

            client = TestClient(create_app())
            payload = {
                "preparationName": "preparation-001",
                "sources": [
                    {
                        "name": "mnist_train",
                        "type": "digit",
                    }
                ],
            }

            response = client.post("/ml/datasets/preparations", json=payload)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.json(),
                {
                    "preparationName": "preparation-001",
                    "createdAtUtc": response.json()["createdAtUtc"],
                    "status": "completed",
                    "sourceReports": [
                        {
                            "name": "mnist_train",
                            "type": "digit",
                            "preparedItemsCount": 2,
                            "rejectedItemsCount": 0,
                            "emptyCellCount": 0,
                        }
                    ],
                    "warnings": [],
                },
            )
            self.assertTrue(
                (
                    preparations_path
                    / "preparation-001"
                    / "digit"
                    / "folders.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    preparations_path
                    / "preparation-001"
                    / "digit"
                    / "mnist_train"
                    / "index.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    preparations_path
                    / "preparation-001"
                    / "digit"
                    / "mnist_train"
                    / "000000.png"
                ).is_file()
            )
            self.assertTrue(
                (
                    preparations_path
                    / "preparation-001"
                    / "digit"
                    / "mnist_train"
                    / "000001.png"
                ).is_file()
            )

    def test_post_preparations_should_return_422_when_source_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            root_path = Path(temp_directory)
            boards_path = root_path / "boards"
            digits_path = root_path / "digits"
            datasets_path = root_path / "datasets"
            previews_path = root_path / "previews"
            preparations_path = root_path / "preparations"
            examples_path = root_path / "examples"
            models_active_path = root_path / "models" / "active"
            models_registry_path = root_path / "models" / "registry"

            boards_path.mkdir(parents=True)
            digits_path.mkdir(parents=True)
            datasets_path.mkdir(parents=True)
            previews_path.mkdir(parents=True)
            preparations_path.mkdir(parents=True)
            examples_path.mkdir(parents=True)
            models_active_path.mkdir(parents=True)
            models_registry_path.mkdir(parents=True)

            os.environ["ML_ENVIRONMENT"] = "local"
            os.environ["ML_BOARDS_SUBDIRECTORY"] = str(boards_path)
            os.environ["ML_DIGITS_SUBDIRECTORY"] = str(digits_path)
            os.environ["ML_TEMP_DATASETS_DIRECTORY_PATH"] = str(datasets_path)
            os.environ["ML_DATASET_PREVIEWS_DIRECTORY_PATH"] = str(
                previews_path
            )
            os.environ["ML_DATASET_PREPARATIONS_DIRECTORY_PATH"] = str(
                preparations_path
            )
            os.environ["ML_EXAMPLES_UPLOADS_DIR"] = str(examples_path)
            os.environ["ML_MODELS_ACTIVE_DIR"] = str(models_active_path)
            os.environ["ML_MODELS_REGISTRY_DIR"] = str(models_registry_path)

            client = TestClient(create_app())
            payload = {
                "preparationName": "preparation-001",
                "sources": [
                    {
                        "name": "mnist_train",
                        "type": "digit",
                    }
                ],
            }

            response = client.post("/ml/datasets/preparations", json=payload)

            self.assertEqual(response.status_code, 422)
            self.assertEqual(response.json()["errorType"], "raw_dataset_not_found")


def _write_idx_pair(images_path: Path, labels_path: Path) -> None:
    image_a = _digit_like_image()
    image_b = _digit_like_image(offset=3)
    images = np.stack((image_a, image_b)).astype(np.uint8)
    labels = np.array([3, 8], dtype=np.uint8)

    images_path.write_bytes(
        struct.pack(">IIII", 2051, images.shape[0], images.shape[1], images.shape[2])
        + images.tobytes()
    )
    labels_path.write_bytes(
        struct.pack(">II", 2049, labels.shape[0]) + labels.tobytes()
    )


def _write_digit_preparation(
    preparations_path: Path,
    preparation_name: str,
    source_name: str,
) -> None:
    source_root = preparations_path / preparation_name / "digit" / source_name
    source_root.mkdir(parents=True, exist_ok=True)
    (source_root.parent / "folders.json").write_text(
        json.dumps([source_name]),
        encoding="utf-8",
    )
    samples = [
        ("000000.png", 3, _digit_like_image()),
        ("000001.png", 8, _digit_like_image(offset=3)),
    ]
    for file_name, _, image in samples:
        cv2.imwrite(str(source_root / file_name), image)
    (source_root / "index.json").write_text(
        json.dumps(
            [
                {"fileName": file_name, "label": label}
                for file_name, label, _ in samples
            ]
        ),
        encoding="utf-8",
    )


def _digit_like_image(offset: int = 0) -> np.ndarray:
    image = np.full((28, 28), 255, dtype=np.uint8)
    image[5 + offset : 21, 12:16] = 0
    image[5 + offset : 9 + offset, 8:20] = 0
    return image


if __name__ == "__main__":
    unittest.main()
