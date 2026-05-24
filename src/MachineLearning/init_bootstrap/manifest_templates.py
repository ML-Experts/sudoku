from copy import deepcopy
from typing import Any

from init_bootstrap.constants import (
    ARTIFACT_FORMAT_PYTORCH_STATE_DICT,
    DEFAULT_PRIMARY_ARTIFACT_RELATIVE_PATH,
    FRAMEWORK_PYTORCH,
)
from init_bootstrap.exceptions import BootstrapConfigurationError
from init_bootstrap.resnet_specs import SUPPORTED_RESNET_SPECS

ManifestTemplate = dict[str, Any]


def _build_resnet_template(model_type: str) -> ManifestTemplate:
    spec = SUPPORTED_RESNET_SPECS[model_type]
    return {
        "framework": FRAMEWORK_PYTORCH,
        "architecture": {
            "type": spec.model_type,
            "family": "resnet",
            "variant": spec.variant,
            "library": "torchvision",
            "pretrainedSource": spec.pretrained_source,
            "numClasses": 10,
            "inputChannels": 3,
            "inputHeight": 224,
            "inputWidth": 224,
            "inputProfile": "default-28x28-v1",
        },
        "artifacts": {
            "primaryArtifactRelativePath": (
                DEFAULT_PRIMARY_ARTIFACT_RELATIVE_PATH
            ),
            "format": ARTIFACT_FORMAT_PYTORCH_STATE_DICT,
        },
        "capabilities": {
            "canStartTraining": True,
            "canUseForInference": False,
        },
        "training": {
            "defaultTrainingProfileName": spec.training_profile_name,
            "defaultAugmentationProfileName": "digits-light-v1",
        },
        "metadata": {
            "createdBy": "init_bootstrap",
            "description": (
                f"{spec.variant} zainicjalizowany z oficjalnych wag "
                "torchvision i zapisany jako lokalny wpis registry."
            ),
        },
    }


MANIFEST_TEMPLATES: dict[tuple[str, str], ManifestTemplate] = {
    ("cnn", "custom-cnn-v1"): {
        "framework": FRAMEWORK_PYTORCH,
        "architecture": {
            "type": "custom-cnn-v1",
            "family": "cnn",
            "variant": "digit-cnn-small",
            "numClasses": 10,
            "inputChannels": 1,
            "inputHeight": 28,
            "inputWidth": 28,
            "inputProfile": "default-28x28-v1",
        },
        "artifacts": {
            "primaryArtifactRelativePath": (
                DEFAULT_PRIMARY_ARTIFACT_RELATIVE_PATH
            ),
            "format": ARTIFACT_FORMAT_PYTORCH_STATE_DICT,
        },
        "capabilities": {
            "canStartTraining": True,
            "canUseForInference": False,
        },
        "training": {
            "defaultTrainingProfileName": "cnn-default-v1",
            "defaultAugmentationProfileName": "digits-light-v1",
        },
        "metadata": {
            "createdBy": "init_bootstrap",
            "description": (
                "Wlasny maly CNN utworzony jako lokalny bootstrap. "
                "Moze wymagac treningu przed uzyciem do inferencji."
            ),
        },
    },
}

for supported_model_type in SUPPORTED_RESNET_SPECS:
    MANIFEST_TEMPLATES[("resnet", supported_model_type)] = (
        _build_resnet_template(supported_model_type)
    )


def get_manifest_template(family: str, model_type: str) -> ManifestTemplate:
    template = MANIFEST_TEMPLATES.get((family, model_type))
    if template is None:
        raise BootstrapConfigurationError(
            error_type="bootstrap_template_not_found",
            message=(
                f"Brak szablonu manifestu dla family='{family}', "
                f"type='{model_type}'."
            ),
        )
    return deepcopy(template)

