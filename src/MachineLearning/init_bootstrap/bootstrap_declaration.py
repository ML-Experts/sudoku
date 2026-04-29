from dataclasses import dataclass
from typing import Any

from init_bootstrap.exceptions import BootstrapConfigurationError
from init_bootstrap.naming import generate_model_name

ALLOWED_DECLARATION_FIELDS = {
    "family",
    "type",
    "name",
    "displayName",
    "canStartTraining",
    "canUseForInference",
}


@dataclass(frozen=True)
class BootstrapModelDeclaration:
    family: str
    model_type: str
    name: str
    display_name: str
    can_start_training: bool | None = None
    can_use_for_inference: bool | None = None


def _get_required_string(raw: dict[str, Any], field_name: str) -> str:
    value = raw.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise BootstrapConfigurationError(
            error_type="bootstrap_configuration_invalid",
            message=f"Deklaracja modelu wymaga pola tekstowego '{field_name}'.",
        )
    return value.strip()


def _get_optional_bool(
    raw: dict[str, Any], field_name: str
) -> bool | None:
    value = raw.get(field_name)
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    raise BootstrapConfigurationError(
        error_type="bootstrap_configuration_invalid",
        message=f"Pole '{field_name}' musi byc wartoscia boolean.",
    )


def parse_bootstrap_declaration(
    raw: dict[str, Any]
) -> BootstrapModelDeclaration:
    unknown_fields = sorted(set(raw.keys()) - ALLOWED_DECLARATION_FIELDS)
    if unknown_fields:
        raise BootstrapConfigurationError(
            error_type="bootstrap_configuration_invalid",
            message=(
                "Deklaracja modelu zawiera niedozwolone pola: "
                f"{', '.join(unknown_fields)}."
            ),
        )

    family = _get_required_string(raw, "family")
    model_type = _get_required_string(raw, "type")
    explicit_name = raw.get("name")
    display_name = raw.get("displayName")

    if explicit_name is not None and not isinstance(explicit_name, str):
        raise BootstrapConfigurationError(
            error_type="bootstrap_configuration_invalid",
            message="Pole 'name' musi byc tekstem.",
        )
    if display_name is not None and not isinstance(display_name, str):
        raise BootstrapConfigurationError(
            error_type="bootstrap_configuration_invalid",
            message="Pole 'displayName' musi byc tekstem.",
        )

    normalized_display_name = (
        display_name.strip()
        if isinstance(display_name, str) and display_name.strip()
        else f"{family} {model_type}"
    )
    model_name = generate_model_name(
        family=family,
        model_type=model_type,
        display_name=normalized_display_name,
        explicit_name=explicit_name.strip()
        if isinstance(explicit_name, str) and explicit_name.strip()
        else None,
    )

    return BootstrapModelDeclaration(
        family=family,
        model_type=model_type,
        name=model_name,
        display_name=normalized_display_name,
        can_start_training=_get_optional_bool(raw, "canStartTraining"),
        can_use_for_inference=_get_optional_bool(raw, "canUseForInference"),
    )

