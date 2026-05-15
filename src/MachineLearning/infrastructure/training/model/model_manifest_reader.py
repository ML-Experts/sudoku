import json
from pathlib import Path

from application.features.trainings.errors.training_run_errors import (
    TrainingRunValidationError,
)
from models.model_manifest import (
    ModelArchitecture,
    ModelArtifacts,
    ModelCapabilities,
    ModelManifest,
)


class ModelManifestReader:
    def read(self, manifest_path: str) -> ModelManifest:
        try:
            raw_manifest = json.loads(Path(manifest_path).read_text("utf-8"))
            architecture = raw_manifest["architecture"]
            artifacts = raw_manifest["artifacts"]
            capabilities = raw_manifest.get("capabilities", {})
            return ModelManifest(
                framework=str(raw_manifest["framework"]),
                architecture=ModelArchitecture(
                    type=str(architecture["type"]),
                    family=str(architecture["family"]),
                    num_classes=int(architecture["numClasses"]),
                    input_channels=int(architecture.get("inputChannels", 1)),
                    input_height=int(architecture.get("inputHeight", 28)),
                    input_width=int(architecture.get("inputWidth", 28)),
                    input_profile=str(architecture["inputProfile"]),
                ),
                artifacts=ModelArtifacts(
                    primary_artifact_relative_path=str(
                        artifacts["primaryArtifactRelativePath"]
                    ),
                    format=str(artifacts["format"]),
                ),
                capabilities=ModelCapabilities(
                    can_start_training=bool(
                        capabilities.get("canStartTraining", False)
                    ),
                    can_use_for_inference=bool(
                        capabilities.get("canUseForInference", False)
                    ),
                ),
                source_type=(
                    str(raw_manifest["sourceType"])
                    if raw_manifest.get("sourceType") is not None
                    else None
                ),
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            raise TrainingRunValidationError(
                "invalid_model_manifest",
                "Manifest modelu nie zawiera wymaganych pól treningowych.",
            ) from error
