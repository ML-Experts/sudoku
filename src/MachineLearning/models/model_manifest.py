from dataclasses import dataclass


@dataclass(frozen=True)
class ModelArchitecture:
    type: str
    family: str
    num_classes: int
    input_channels: int
    input_height: int
    input_width: int
    input_profile: str


@dataclass(frozen=True)
class ModelArtifacts:
    primary_artifact_relative_path: str
    format: str


@dataclass(frozen=True)
class ModelCapabilities:
    can_start_training: bool
    can_use_for_inference: bool


@dataclass(frozen=True)
class ModelManifest:
    framework: str
    architecture: ModelArchitecture
    artifacts: ModelArtifacts
    capabilities: ModelCapabilities
    source_type: str | None = None
