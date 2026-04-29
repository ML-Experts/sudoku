import argparse
from pathlib import Path

from init_bootstrap.bootstrap_models import BootstrapModelsApplication
from init_bootstrap.env_loader import load_environment
from init_bootstrap.exceptions import BootstrapError
from init_bootstrap.logging_config import configure_logging
from init_bootstrap.settings import load_bootstrap_settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m init_bootstrap",
        description="Inicjalizuje bootstrap modeli ML w lokalnym registry.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Pokaz planowane akcje bez zapisu do registry.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Wlacz bardziej szczegolowe logowanie konsolowe.",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=None,
        help="Opcjonalna sciezka do pliku env uzywana w testach operacyjnych.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    configure_logging(args.verbose)

    try:
        environment_values = load_environment(env_file=args.env_file)
        settings = load_bootstrap_settings(environment_values)
        result = BootstrapModelsApplication().run(
            settings, dry_run=args.dry_run
        )
    except BootstrapError as error:
        print(f"{error.error_type}: {error.message}")
        return 1

    print(result.to_text())
    return 1 if result.has_failures else 0

