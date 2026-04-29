from typing import Any

from init_bootstrap.exceptions import BootstrapConfigurationError
from init_bootstrap.resnet_specs import is_supported_resnet


def build_model_for_manifest(manifest: dict[str, Any]) -> Any:
    architecture_type = manifest["architecture"]["type"]

    if architecture_type == "custom-cnn-v1":
        from init_bootstrap.custom_cnn import build_custom_cnn_v1

        return build_custom_cnn_v1(manifest)

    if is_supported_resnet(architecture_type):
        from init_bootstrap.torchvision_resnet import build_torchvision_resnet

        return build_torchvision_resnet(manifest)

    raise BootstrapConfigurationError(
        error_type="bootstrap_model_builder_not_found",
        message=f"Brak buildera dla architecture.type='{architecture_type}'.",
    )

