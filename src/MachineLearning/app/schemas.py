from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RuntimeStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    message: str
    service: str
    version: str
    environment: str
    timestamp_utc: datetime
