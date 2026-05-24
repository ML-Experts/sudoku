from dataclasses import dataclass


@dataclass(frozen=True)
class InferenceRuntimeModelReferenceDto:
    name: str
    manifest_path: str
    primary_artifact_path: str
    input_profile: str
