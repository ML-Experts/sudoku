from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RuntimeStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    message: str
    service: str
    service_slug: str
    version: str
    environment: str
    dependency_name: str
    dependency_version: str
    timestamp_utc: datetime
