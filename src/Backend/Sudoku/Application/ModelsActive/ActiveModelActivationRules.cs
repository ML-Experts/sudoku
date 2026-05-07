using FluentValidation.Results;
using Sudoku.Application.ModelsRegistry;

namespace Sudoku.Application.ModelsActive;

internal static class ActiveModelActivationRules
{
    public const int MaxModelNameLength = 128;

    private const string ArtifactMissingWarning = "model_artifacts_missing";
    private const string PrimaryArtifactMissingWarning = "primary_artifact_missing";

    public static ValidationFailure? ValidateModelName(string? modelName, string propertyName)
    {
        if (string.IsNullOrWhiteSpace(modelName))
        {
            return CreateInvalidRequestFailure(propertyName, "Nazwa modelu jest wymagana.");
        }

        var trimmedModelName = modelName.Trim();
        if (trimmedModelName.Length > MaxModelNameLength)
        {
            return CreateInvalidRequestFailure(
                propertyName,
                $"Nazwa modelu nie może być dłuższa niż {MaxModelNameLength} znaków.");
        }

        if (trimmedModelName is "." or ".."
            || trimmedModelName.Contains("..", StringComparison.Ordinal)
            || trimmedModelName.Contains(':', StringComparison.Ordinal)
            || trimmedModelName.Contains('/', StringComparison.Ordinal)
            || trimmedModelName.Contains('\\', StringComparison.Ordinal)
            || trimmedModelName.IndexOfAny(Path.GetInvalidFileNameChars()) >= 0
            || trimmedModelName.Any(char.IsControl))
        {
            return CreateInvalidRequestFailure(propertyName, "Nazwa modelu zawiera niedozwolone znaki.");
        }

        return null;
    }

    public static void EnsureCanUseForInference(RegistryModelManifestDto model)
    {
        if (!model.CanUseForInference)
        {
            throw new ActiveModelCannotUseForInferenceException(model.Name);
        }
    }

    public static void EnsureActivatableManifest(RegistryModelManifestDto model)
    {
        if (string.IsNullOrWhiteSpace(model.Name)
            || string.IsNullOrWhiteSpace(model.DisplayName)
            || string.IsNullOrWhiteSpace(model.SourceType)
            || string.IsNullOrWhiteSpace(model.InputProfile)
            || string.IsNullOrWhiteSpace(model.PrimaryArtifactRelativePath))
        {
            throw new ActiveModelManifestInvalidException(
                model.Name,
                $"Manifest modelu {model.Name} nie zawiera pól wymaganych do aktywacji.");
        }

        if (Path.IsPathRooted(model.PrimaryArtifactRelativePath)
            || ContainsParentDirectorySegment(model.PrimaryArtifactRelativePath))
        {
            throw new ActiveModelManifestInvalidException(
                model.Name,
                $"Manifest modelu {model.Name} zawiera niebezpieczną ścieżkę artefaktu.");
        }

        if (model.Warnings.Any(IsBlockingWarning))
        {
            throw new ActiveModelManifestInvalidException(
                model.Name,
                $"Manifest modelu {model.Name} wskazuje niekompletne artefakty inferencyjne.");
        }
    }

    private static ValidationFailure CreateInvalidRequestFailure(string propertyName, string message)
    {
        return new ValidationFailure(propertyName, message)
        {
            ErrorCode = SetActiveModelErrorTypes.InvalidRequest
        };
    }

    private static bool ContainsParentDirectorySegment(string relativePath)
    {
        return relativePath
            .Split(
                new[] { '/', '\\' },
                StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries)
            .Any(segment => segment == "..");
    }

    private static bool IsBlockingWarning(string warning)
    {
        return string.Equals(warning, ArtifactMissingWarning, StringComparison.Ordinal)
               || string.Equals(warning, PrimaryArtifactMissingWarning, StringComparison.Ordinal);
    }
}
