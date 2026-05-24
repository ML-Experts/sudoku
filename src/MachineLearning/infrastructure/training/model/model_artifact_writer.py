from pathlib import Path

import torch
from torch import nn

from models.model_manifest import ModelManifest


class ModelArtifactWriter:
    def write(
        self,
        model: nn.Module,
        output_model_directory_path: str,
        manifest: ModelManifest,
    ) -> str:
        relative_path = manifest.artifacts.primary_artifact_relative_path
        output_path = Path(output_model_directory_path) / relative_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(model.state_dict(), output_path)
        return relative_path
