from dataclasses import dataclass


@dataclass(frozen=True)
class ActiveModelReferenceDto:
    model_name: str
    model_directory_path: str
    manifest_path: str
    primary_artifact_path: str
