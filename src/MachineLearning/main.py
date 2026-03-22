import sys
from pathlib import Path


if __package__ in {None, ""}:
    project_dir = Path(__file__).resolve().parent
    project_dir_as_text = str(project_dir)
    if project_dir_as_text not in sys.path:
        sys.path.insert(0, project_dir_as_text)

from api.main import app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)

__all__ = ["app"]
