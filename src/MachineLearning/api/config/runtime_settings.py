from dataclasses import dataclass


@dataclass(frozen=True)
class RuntimeSettings:
    environment: str
    service_name: str
    service_version: str
    ping_response_message: str
