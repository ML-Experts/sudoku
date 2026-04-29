from dataclasses import dataclass


@dataclass(frozen=True)
class ResNetSpec:
    model_type: str
    variant: str
    builder_name: str
    weights_class_name: str
    training_profile_name: str

    @property
    def pretrained_source(self) -> str:
        return f"{self.weights_class_name}.DEFAULT"


SUPPORTED_RESNET_SPECS: dict[str, ResNetSpec] = {
    "resnet18": ResNetSpec(
        model_type="resnet18",
        variant="resnet18",
        builder_name="resnet18",
        weights_class_name="ResNet18_Weights",
        training_profile_name="resnet18-finetune-v1",
    ),
    "resnet34": ResNetSpec(
        model_type="resnet34",
        variant="resnet34",
        builder_name="resnet34",
        weights_class_name="ResNet34_Weights",
        training_profile_name="resnet34-finetune-v1",
    ),
    "resnet50": ResNetSpec(
        model_type="resnet50",
        variant="resnet50",
        builder_name="resnet50",
        weights_class_name="ResNet50_Weights",
        training_profile_name="resnet50-finetune-v1",
    ),
    "resnet101": ResNetSpec(
        model_type="resnet101",
        variant="resnet101",
        builder_name="resnet101",
        weights_class_name="ResNet101_Weights",
        training_profile_name="resnet101-finetune-v1",
    ),
    "resnet152": ResNetSpec(
        model_type="resnet152",
        variant="resnet152",
        builder_name="resnet152",
        weights_class_name="ResNet152_Weights",
        training_profile_name="resnet152-finetune-v1",
    ),
    "wide_resnet50_2": ResNetSpec(
        model_type="wide_resnet50_2",
        variant="wide_resnet50_2",
        builder_name="wide_resnet50_2",
        weights_class_name="Wide_ResNet50_2_Weights",
        training_profile_name="wide-resnet50-2-finetune-v1",
    ),
    "wide_resnet101_2": ResNetSpec(
        model_type="wide_resnet101_2",
        variant="wide_resnet101_2",
        builder_name="wide_resnet101_2",
        weights_class_name="Wide_ResNet101_2_Weights",
        training_profile_name="wide-resnet101-2-finetune-v1",
    ),
}


def is_supported_resnet(model_type: str) -> bool:
    return model_type in SUPPORTED_RESNET_SPECS

