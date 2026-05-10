from enum import StrEnum


class ReportStatus(StrEnum):
    READY = "ready"
    MISSING = "missing"
    CORRUPTED = "corrupted"
