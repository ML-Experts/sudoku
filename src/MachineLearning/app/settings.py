from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class MlSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="ML_",
        case_sensitive=False,
        extra="ignore",
    )

    service_name: str = "sudoku-ml"
    service_version: str = "0.1.0"
    environment: str = "production"
    ping_response_message: str = "pong"

    data_raw_dir: Path | None = None
    data_processed_dir: Path | None = None
    data_benchmark_dir: Path | None = None
    models_active_dir: Path | None = None
    models_registry_dir: Path | None = None
    trainings_runs_dir: Path | None = None
    trainings_reports_dir: Path | None = None
    trainings_metadata_dir: Path | None = None
    examples_uploads_dir: Path | None = None
    examples_generated_dir: Path | None = None
    tmp_dir: Path | None = None


@lru_cache
def get_settings() -> MlSettings:
    return MlSettings()
