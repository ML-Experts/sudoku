import sys
from pathlib import Path


if __package__ in {None, ""}:
    src_dir = Path(__file__).resolve().parents[1]
    src_dir_as_text = str(src_dir)
    if src_dir_as_text not in sys.path:
        sys.path.insert(0, src_dir_as_text)

from MachineLearning.api.main import app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)

__all__ = ["app"]
