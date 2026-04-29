import json
from pathlib import Path
from typing import Any

Manifest = dict[str, Any]


def read_manifest(path: Path) -> Manifest:
    with path.open("r", encoding="utf-8") as file:
        value = json.load(file)

    if not isinstance(value, dict):
        raise ValueError("Manifest JSON must be an object.")

    return value


def write_manifest(path: Path, manifest: Manifest) -> None:
    path.write_text(
        json.dumps(manifest, ensure_ascii=True, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )

