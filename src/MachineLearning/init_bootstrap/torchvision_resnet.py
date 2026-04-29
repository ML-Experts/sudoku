from typing import Any

from init_bootstrap.exceptions import (
    BootstrapDependencyMissingError,
    BootstrapConfigurationError,
    BootstrapPretrainedWeightsUnavailableError,
)
from init_bootstrap.resnet_specs import SUPPORTED_RESNET_SPECS


def build_torchvision_resnet(manifest: dict[str, Any]) -> Any:
    try:
        import torch.nn as nn
        import torchvision.models as torchvision_models
    except ImportError as error:
        dependency = "torchvision" if "torchvision" in str(error) else "torch"
        raise BootstrapDependencyMissingError(dependency) from error

    architecture = manifest["architecture"]
    architecture_type = architecture["type"]
    num_classes = int(architecture["numClasses"])
    pretrained_source = architecture.get("pretrainedSource")
    spec = SUPPORTED_RESNET_SPECS.get(architecture_type)

    if spec is None:
        raise BootstrapConfigurationError(
            error_type="bootstrap_model_builder_not_found",
            message=(
                "Brak buildera torchvision ResNet dla "
                f"architecture.type='{architecture_type}'."
            ),
        )

    model_builder = getattr(torchvision_models, spec.builder_name)
    weights_class = getattr(torchvision_models, spec.weights_class_name)
    weights = None

    if pretrained_source == spec.pretrained_source:
        weights = weights_class.DEFAULT

    try:
        model = model_builder(weights=weights, progress=False)
    except Exception as error:
        raise BootstrapPretrainedWeightsUnavailableError(
            "Nie udalo sie pobrac albo odczytac oficjalnych wag "
            f"{spec.variant}. "
            "Uruchom init ponownie z dostepem do cache/internetu albo "
            "sprawdz instalacje torchvision."
        ) from error

    model.fc = nn.Linear(model.fc.in_features, num_classes)
    return model

