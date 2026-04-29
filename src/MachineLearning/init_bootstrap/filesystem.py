import os
import shutil
from pathlib import Path


def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def remove_directory(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)


def replace_directory(source: Path, target: Path) -> None:
    backup = target.with_name(f".{target.name}.old")
    if backup.exists():
        shutil.rmtree(backup)

    if target.exists():
        os.replace(target, backup)

    try:
        os.replace(source, target)
    except Exception:
        if backup.exists() and not target.exists():
            os.replace(backup, target)
        raise
    else:
        if backup.exists():
            shutil.rmtree(backup)


def move_directory(source: Path, target: Path) -> None:
    os.replace(source, target)

