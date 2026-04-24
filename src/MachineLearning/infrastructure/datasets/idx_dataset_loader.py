import struct
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class DigitDatasetRecord:
    sample_key: str
    image: NDArray[np.uint8]
    label: int


class IdxDatasetLoader:
    def load(
        self, images_path: Path, labels_path: Path
    ) -> tuple[DigitDatasetRecord, ...]:
        images = self._read_idx_images(images_path)
        labels = self._read_idx_labels(labels_path)

        if images.shape[0] != labels.shape[0]:
            raise ValueError(
                "Liczba obrazów IDX nie zgadza się z liczbą etykiet IDX."
            )

        records = [
            DigitDatasetRecord(
                sample_key=str(index),
                image=images[index],
                label=int(labels[index]),
            )
            for index in range(images.shape[0])
        ]
        return tuple(records)

    def _read_idx_images(self, file_path: Path) -> NDArray[np.uint8]:
        raw_bytes = file_path.read_bytes()
        if len(raw_bytes) < 16:
            raise ValueError("Plik IDX obrazów ma niepoprawny nagłówek.")

        magic, count, rows, cols = struct.unpack(">IIII", raw_bytes[:16])
        if magic != 2051:
            raise ValueError("Plik obrazów nie ma poprawnego magic number IDX.")

        expected_size = 16 + count * rows * cols
        if len(raw_bytes) != expected_size:
            raise ValueError("Plik obrazów IDX ma niepoprawny rozmiar.")

        data = np.frombuffer(raw_bytes[16:], dtype=np.uint8)
        return data.reshape((count, rows, cols))

    def _read_idx_labels(self, file_path: Path) -> NDArray[np.uint8]:
        raw_bytes = file_path.read_bytes()
        if len(raw_bytes) < 8:
            raise ValueError("Plik IDX etykiet ma niepoprawny nagłówek.")

        magic, count = struct.unpack(">II", raw_bytes[:8])
        if magic != 2049:
            raise ValueError("Plik etykiet nie ma poprawnego magic number IDX.")

        expected_size = 8 + count
        if len(raw_bytes) != expected_size:
            raise ValueError("Plik etykiet IDX ma niepoprawny rozmiar.")

        return np.frombuffer(raw_bytes[8:], dtype=np.uint8)
