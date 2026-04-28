class PrepareDatasetArtifactCommandError(Exception):
    def __init__(self, error_type: str, message: str) -> None:
        super().__init__(message)
        self.error_type = error_type
        self.message = message


class UnsupportedPreprocessingProfileError(
    PrepareDatasetArtifactCommandError
):
    def __init__(self, profile_name: str) -> None:
        super().__init__(
            error_type="unsupported_preprocessing_profile",
            message=(
                f"Profil preprocessingu {profile_name} nie jest obsługiwany."
            ),
        )
