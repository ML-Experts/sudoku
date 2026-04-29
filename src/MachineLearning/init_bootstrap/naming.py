import re
import unicodedata

from init_bootstrap.exceptions import BootstrapConfigurationError

MODEL_NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def slug_model_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    slug = ascii_value.lower()
    slug = re.sub(r"[^a-z0-9-]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug


def validate_model_name(model_name: str) -> None:
    if not MODEL_NAME_PATTERN.fullmatch(model_name):
        raise BootstrapConfigurationError(
            error_type="bootstrap_model_name_invalid",
            message=(
                f"Nazwa modelu '{model_name}' musi pasowac do formatu "
                "[a-z0-9-]+ bez separatorow na poczatku i koncu."
            ),
        )


def generate_model_name(
    family: str,
    model_type: str,
    display_name: str | None = None,
    explicit_name: str | None = None,
) -> str:
    if explicit_name:
        candidate = explicit_name
    elif display_name:
        candidate = display_name
    else:
        candidate = f"{family}-{model_type}"

    model_name = slug_model_name(candidate)
    validate_model_name(model_name)
    return model_name


def ensure_unique_model_names(model_names: list[str]) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()

    for model_name in model_names:
        if model_name in seen:
            duplicates.add(model_name)
        seen.add(model_name)

    if duplicates:
        duplicate_names = ", ".join(sorted(duplicates))
        raise BootstrapConfigurationError(
            error_type="bootstrap_model_name_collision",
            message=(
                "Deklaracje bootstrap prowadza do zdublowanych nazw: "
                f"{duplicate_names}."
            ),
        )

