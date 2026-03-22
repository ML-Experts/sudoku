from datetime import UTC, datetime


class SystemUtcClock:
    def now_utc(self) -> datetime:
        return datetime.now(UTC)
