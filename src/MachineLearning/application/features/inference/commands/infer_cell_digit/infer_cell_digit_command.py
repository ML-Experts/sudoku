from dataclasses import dataclass

from application.features.inference.dto.inference_runtime_configuration_dto import (
    InferenceRuntimeConfigurationDto,
)
from application.features.inference.dto.inference_runtime_model_reference_dto import (
    InferenceRuntimeModelReferenceDto,
)


@dataclass(frozen=True)
class InferCellDigitCommand:
    mime_type: str
    base64_image: str
    active_model: InferenceRuntimeModelReferenceDto
    resolved_configuration: InferenceRuntimeConfigurationDto
