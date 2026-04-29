class BootstrapError(Exception):
    def __init__(
        self,
        error_type: str,
        message: str,
        *,
        is_fatal: bool = True,
    ) -> None:
        super().__init__(message)
        self.error_type = error_type
        self.message = message
        self.is_fatal = is_fatal


class BootstrapConfigurationError(BootstrapError):
    def __init__(self, error_type: str, message: str) -> None:
        super().__init__(error_type=error_type, message=message)


class BootstrapDependencyMissingError(BootstrapError):
    def __init__(self, dependency_name: str) -> None:
        super().__init__(
            error_type="bootstrap_dependency_missing",
            message=(
                f"Brakuje zaleznosci '{dependency_name}'. Zainstaluj pakiety "
                "komenda: pip install -r src/MachineLearning/requirements.txt"
            ),
        )


class BootstrapPretrainedWeightsUnavailableError(BootstrapError):
    def __init__(self, message: str) -> None:
        super().__init__(
            error_type="bootstrap_pretrained_weights_unavailable",
            message=message,
        )


class BootstrapRegistryError(BootstrapError):
    pass


class BootstrapRegistryEntryIncompleteError(BootstrapRegistryError):
    def __init__(self, model_name: str, reasons: list[str]) -> None:
        details = ", ".join(reasons)
        super().__init__(
            error_type="bootstrap_registry_entry_incomplete",
            message=(
                f"Wpis registry '{model_name}' jest niekompletny: {details}."
            ),
        )


class BootstrapRegistryEntryAlreadyExistsError(BootstrapRegistryError):
    def __init__(self, model_name: str) -> None:
        super().__init__(
            error_type="bootstrap_registry_entry_already_exists",
            message=(
                f"Wpis registry '{model_name}' juz istnieje i overwrite "
                "nie zostal wlaczony."
            ),
        )

