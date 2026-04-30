from enum import StrEnum


class TrainingRunEventType(StrEnum):
    STATUS_CHANGED = "statusChanged"
    PROGRESS = "progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
