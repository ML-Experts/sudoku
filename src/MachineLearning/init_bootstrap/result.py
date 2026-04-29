from dataclasses import dataclass, field

from init_bootstrap.constants import (
    STATUS_CREATED,
    STATUS_FAILED,
    STATUS_SKIPPED,
)


@dataclass(frozen=True)
class BootstrapModelResult:
    model_name: str
    status: str
    reason: str | None = None
    error_type: str | None = None
    message: str | None = None

    @classmethod
    def created(cls, model_name: str) -> "BootstrapModelResult":
        return cls(model_name=model_name, status=STATUS_CREATED)

    @classmethod
    def skipped(
        cls, model_name: str, reason: str
    ) -> "BootstrapModelResult":
        return cls(model_name=model_name, status=STATUS_SKIPPED, reason=reason)

    @classmethod
    def failed(
        cls,
        model_name: str,
        error_type: str,
        message: str,
    ) -> "BootstrapModelResult":
        return cls(
            model_name=model_name,
            status=STATUS_FAILED,
            error_type=error_type,
            message=message,
        )


@dataclass(frozen=True)
class ActiveModelResult:
    status: str
    reason: str | None = None
    model_name: str | None = None
    message: str | None = None


@dataclass(frozen=True)
class BootstrapRunResult:
    model_results: list[BootstrapModelResult] = field(default_factory=list)
    active_model_result: ActiveModelResult | None = None

    @property
    def has_failures(self) -> bool:
        return any(result.status == STATUS_FAILED for result in self.model_results)

    def to_text(self) -> str:
        lines = ["Bootstrap modeli ML:"]
        for result in self.model_results:
            details = result.reason or result.error_type or "ok"
            if result.message:
                details = f"{details}: {result.message}"
            lines.append(f"- {result.model_name}: {result.status} ({details})")

        if self.active_model_result is not None:
            active = self.active_model_result
            details = active.reason or active.message or "ok"
            model_name = active.model_name or "-"
            lines.append(
                f"Aktywny model: {active.status} ({model_name}, {details})"
            )

        return "\n".join(lines)

