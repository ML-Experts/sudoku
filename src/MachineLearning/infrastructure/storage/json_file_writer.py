import json
from pathlib import Path
from typing import Any


class JsonFileWriter:
    def write(self, path: Path, payload: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = path.with_suffix(f"{path.suffix}.tmp")
        temporary_path.write_text(
            json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=False) + "\n",
            encoding="utf-8",
        )
        temporary_path.replace(path)
