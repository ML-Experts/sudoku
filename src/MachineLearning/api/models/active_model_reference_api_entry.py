from pydantic import BaseModel, ConfigDict, Field


class ActiveModelReferenceApiEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    name: str = Field(min_length=1)
    manifest_path: str = Field(alias="manifestPath", min_length=1)
    primary_artifact_path: str = Field(
        alias="primaryArtifactPath",
        min_length=1,
    )
    input_profile: str = Field(alias="inputProfile", min_length=1)
