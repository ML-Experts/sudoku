from typing import Any, Callable

from init_bootstrap.active_model_writer import ensure_active_model_if_missing
from init_bootstrap.exceptions import (
    BootstrapError,
    BootstrapRegistryEntryIncompleteError,
)
from init_bootstrap.manifest_builder import build_manifest
from init_bootstrap.model_builders import build_model_for_manifest
from init_bootstrap.registry_inspector import inspect_registry_entry
from init_bootstrap.registry_writer import (
    ArtifactSerializer,
    write_registry_entry,
)
from init_bootstrap.result import BootstrapModelResult, BootstrapRunResult
from init_bootstrap.settings import BootstrapSettings

ModelBuilder = Callable[[dict[str, Any]], Any]


class BootstrapModelsApplication:
    def __init__(
        self,
        *,
        model_builder: ModelBuilder = build_model_for_manifest,
        artifact_serializer: ArtifactSerializer | None = None,
    ) -> None:
        self._model_builder = model_builder
        self._artifact_serializer = artifact_serializer

    def run(
        self, settings: BootstrapSettings, *, dry_run: bool = False
    ) -> BootstrapRunResult:
        model_results: list[BootstrapModelResult] = []

        for declaration in settings.declarations:
            try:
                manifest = build_manifest(declaration)
                inspection = inspect_registry_entry(
                    settings.registry_directory_path, manifest
                )

                if inspection.is_complete and not settings.overwrite_existing:
                    model_results.append(
                        BootstrapModelResult.skipped(
                            declaration.name, "entry_complete"
                        )
                    )
                    continue

                if inspection.is_incomplete and not settings.overwrite_existing:
                    raise BootstrapRegistryEntryIncompleteError(
                        declaration.name, inspection.reasons
                    )

                if dry_run:
                    reason = (
                        "dry_run_would_overwrite"
                        if settings.overwrite_existing
                        and not inspection.is_missing
                        else "dry_run_would_create"
                    )
                    model_results.append(
                        BootstrapModelResult.skipped(declaration.name, reason)
                    )
                    continue

                model = self._model_builder(manifest)
                write_registry_entry(
                    settings.registry_directory_path,
                    manifest,
                    model,
                    overwrite=settings.overwrite_existing,
                    **(
                        {"artifact_serializer": self._artifact_serializer}
                        if self._artifact_serializer is not None
                        else {}
                    ),
                )
                model_results.append(
                    BootstrapModelResult.created(declaration.name)
                )
            except BootstrapError as error:
                model_results.append(
                    BootstrapModelResult.failed(
                        declaration.name,
                        error.error_type,
                        error.message,
                    )
                )
                if error.is_fatal:
                    break

        active_result = None
        if not dry_run:
            active_result = ensure_active_model_if_missing(
                active_model_directory_path=settings.active_model_directory_path,
                registry_directory_path=settings.registry_directory_path,
                default_active_model=settings.default_active_model,
                set_active_if_missing=settings.set_active_if_missing,
            )

        return BootstrapRunResult(
            model_results=model_results,
            active_model_result=active_result,
        )

