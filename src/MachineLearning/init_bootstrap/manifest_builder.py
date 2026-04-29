from typing import Any

from init_bootstrap.bootstrap_declaration import BootstrapModelDeclaration
from init_bootstrap.constants import SOURCE_TYPE_BOOTSTRAP
from init_bootstrap.manifest_templates import get_manifest_template
from init_bootstrap.validation import validate_manifest_contract

Manifest = dict[str, Any]


def build_manifest(declaration: BootstrapModelDeclaration) -> Manifest:
    manifest = get_manifest_template(
        declaration.family, declaration.model_type
    )
    capabilities = dict(manifest["capabilities"])

    if declaration.can_start_training is not None:
        capabilities["canStartTraining"] = declaration.can_start_training
    if declaration.can_use_for_inference is not None:
        capabilities["canUseForInference"] = declaration.can_use_for_inference

    manifest = {
        "name": declaration.name,
        "displayName": declaration.display_name,
        "sourceType": SOURCE_TYPE_BOOTSTRAP,
        "sourceRunName": None,
        "framework": manifest["framework"],
        "architecture": manifest["architecture"],
        "artifacts": manifest["artifacts"],
        "capabilities": capabilities,
        "training": manifest["training"],
        "metadata": manifest["metadata"],
    }
    validate_manifest_contract(manifest)
    return manifest

