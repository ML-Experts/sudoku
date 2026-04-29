import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from init_bootstrap.bootstrap_declaration import (
    BootstrapModelDeclaration,
    parse_bootstrap_declaration,
)
from init_bootstrap.constants import (
    ACTIVE_MODEL_DIRECTORY_VARIABLE_NAMES,
    BOOTSTRAP_DEFAULT_ACTIVE_MODEL_VARIABLE_NAME,
    BOOTSTRAP_MODELS_JSON_VARIABLE_NAME,
    BOOTSTRAP_OVERWRITE_EXISTING_VARIABLE_NAME,
    BOOTSTRAP_SET_ACTIVE_IF_MISSING_VARIABLE_NAME,
    REGISTRY_DIRECTORY_VARIABLE_NAMES,
)
from init_bootstrap.exceptions import BootstrapConfigurationError
from init_bootstrap.naming import ensure_unique_model_names


@dataclass(frozen=True)
class BootstrapSettings:
    registry_directory_path: Path
    active_model_directory_path: Path
    declarations: list[BootstrapModelDeclaration]
    overwrite_existing: bool
    set_active_if_missing: bool
    default_active_model: str | None


def _get_required_value(
    values: dict[str, str], variable_names: tuple[str, ...]
) -> str:
    for variable_name in variable_names:
        value = values.get(variable_name)
        if value is not None and value.strip():
            return value.strip()

    raise BootstrapConfigurationError(
        error_type="bootstrap_configuration_missing",
        message=(
            "Brakuje wymaganej zmiennej konfiguracji. Akceptowane nazwy: "
            f"{', '.join(variable_names)}."
        ),
    )


def _parse_bool(values: dict[str, str], variable_name: str) -> bool:
    value = values.get(variable_name)
    if value is None:
        raise BootstrapConfigurationError(
            error_type="bootstrap_configuration_missing",
            message=f"Brakuje wymaganej zmiennej '{variable_name}'.",
        )

    normalized = value.strip().lower()
    if normalized in {"true", "1", "yes", "y"}:
        return True
    if normalized in {"false", "0", "no", "n"}:
        return False

    raise BootstrapConfigurationError(
        error_type="bootstrap_configuration_invalid",
        message=f"Zmienna '{variable_name}' musi byc wartoscia boolean.",
    )


def _parse_absolute_path(raw_path: str, variable_name: str) -> Path:
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        raise BootstrapConfigurationError(
            error_type="bootstrap_configuration_invalid",
            message=f"Zmienna '{variable_name}' musi byc sciezka absolutna.",
        )
    return path


def _parse_declarations(raw_json: str) -> list[BootstrapModelDeclaration]:
    try:
        raw_values: Any = json.loads(raw_json)
    except json.JSONDecodeError as error:
        raise BootstrapConfigurationError(
            error_type="bootstrap_configuration_invalid",
            message=(
                f"Zmienna '{BOOTSTRAP_MODELS_JSON_VARIABLE_NAME}' nie jest "
                f"poprawnym JSON: {error.msg}."
            ),
        ) from error

    if not isinstance(raw_values, list) or not raw_values:
        raise BootstrapConfigurationError(
            error_type="bootstrap_configuration_invalid",
            message=(
                f"Zmienna '{BOOTSTRAP_MODELS_JSON_VARIABLE_NAME}' musi byc "
                "niepusta lista obiektow."
            ),
        )

    declarations: list[BootstrapModelDeclaration] = []
    for raw_value in raw_values:
        if not isinstance(raw_value, dict):
            raise BootstrapConfigurationError(
                error_type="bootstrap_configuration_invalid",
                message="Kazda deklaracja modelu musi byc obiektem JSON.",
            )
        declarations.append(parse_bootstrap_declaration(raw_value))

    ensure_unique_model_names(
        [declaration.name for declaration in declarations]
    )
    return declarations


def load_bootstrap_settings(values: dict[str, str]) -> BootstrapSettings:
    registry_raw = _get_required_value(values, REGISTRY_DIRECTORY_VARIABLE_NAMES)
    active_raw = _get_required_value(
        values, ACTIVE_MODEL_DIRECTORY_VARIABLE_NAMES
    )
    models_json = values.get(BOOTSTRAP_MODELS_JSON_VARIABLE_NAME)
    if models_json is None or not models_json.strip():
        raise BootstrapConfigurationError(
            error_type="bootstrap_configuration_missing",
            message=(
                f"Brakuje wymaganej zmiennej "
                f"'{BOOTSTRAP_MODELS_JSON_VARIABLE_NAME}'."
            ),
        )

    default_active_model = values.get(
        BOOTSTRAP_DEFAULT_ACTIVE_MODEL_VARIABLE_NAME
    )
    normalized_default_active = (
        default_active_model.strip()
        if default_active_model is not None and default_active_model.strip()
        else None
    )

    return BootstrapSettings(
        registry_directory_path=_parse_absolute_path(
            registry_raw, REGISTRY_DIRECTORY_VARIABLE_NAMES[0]
        ),
        active_model_directory_path=_parse_absolute_path(
            active_raw, ACTIVE_MODEL_DIRECTORY_VARIABLE_NAMES[0]
        ),
        declarations=_parse_declarations(models_json),
        overwrite_existing=_parse_bool(
            values, BOOTSTRAP_OVERWRITE_EXISTING_VARIABLE_NAME
        ),
        set_active_if_missing=_parse_bool(
            values, BOOTSTRAP_SET_ACTIVE_IF_MISSING_VARIABLE_NAME
        ),
        default_active_model=normalized_default_active,
    )

