using Sudoku.Application.ModelsRegistry;

namespace Sudoku.Application.ModelsActive;

public sealed record ResolvedActiveModelDto(
    ActiveModelPointerDto Pointer,
    RegistryModelManifestDto Manifest,
    string ManifestPath,
    string PrimaryArtifactPath);
