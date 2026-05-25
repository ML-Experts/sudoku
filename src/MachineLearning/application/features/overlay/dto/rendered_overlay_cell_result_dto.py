from dataclasses import dataclass


@dataclass(frozen=True)
class RenderedOverlayCellResultDto:
    mime_type: str
    base64: str
