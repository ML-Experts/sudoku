from dataclasses import dataclass


@dataclass(frozen=True)
class PreprocessBoardCommandResultDto:
    mime_type: str
    base64: str
