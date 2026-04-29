from typing import Any

from init_bootstrap.exceptions import BootstrapDependencyMissingError


def build_custom_cnn_v1(manifest: dict[str, Any]) -> Any:
    try:
        import torch.nn as nn
    except ImportError as error:
        raise BootstrapDependencyMissingError("torch") from error

    architecture = manifest["architecture"]
    input_channels = int(architecture["inputChannels"])
    num_classes = int(architecture["numClasses"])

    class CustomDigitCnnV1(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.features = nn.Sequential(
                nn.Conv2d(input_channels, 32, kernel_size=3, padding=1),
                nn.ReLU(inplace=True),
                nn.MaxPool2d(kernel_size=2),
                nn.Conv2d(32, 64, kernel_size=3, padding=1),
                nn.ReLU(inplace=True),
                nn.MaxPool2d(kernel_size=2),
            )
            self.classifier = nn.Sequential(
                nn.Flatten(),
                nn.Linear(64 * 7 * 7, 128),
                nn.ReLU(inplace=True),
                nn.Dropout(p=0.25),
                nn.Linear(128, num_classes),
            )

        def forward(self, x: Any) -> Any:
            return self.classifier(self.features(x))

    return CustomDigitCnnV1()

