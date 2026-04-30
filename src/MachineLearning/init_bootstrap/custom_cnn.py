from typing import Any

from init_bootstrap.exceptions import BootstrapDependencyMissingError


def build_custom_cnn_v1(manifest: dict[str, Any]) -> Any:
    try:
        from infrastructure.training.model.custom_digit_cnn_v1 import (
            CustomDigitCnnV1,
        )
    except ImportError as error:
        raise BootstrapDependencyMissingError("torch") from error

    architecture = manifest["architecture"]
    input_channels = int(architecture["inputChannels"])
    num_classes = int(architecture["numClasses"])
    return CustomDigitCnnV1(
        num_classes=num_classes,
        input_channels=input_channels,
    )

