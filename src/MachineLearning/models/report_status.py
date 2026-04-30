from enum import StrEnum


class ReportStatus(StrEnum):
    OK = "ok"
    MISSING = "missing"
    CORRUPTED = "corrupted"
