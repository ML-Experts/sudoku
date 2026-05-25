from dataclasses import dataclass


@dataclass(frozen=True)
class RenderOverlayCellCommandResultDto:
    mime_type: str
    base64: str
