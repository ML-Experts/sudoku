using System.Text.Json;
using System.Text;
using Microsoft.Extensions.Options;
using Sudoku.Application.Abstractions;
using Sudoku.Application.ModelsRegistry;
using Sudoku.Application.Storage;

namespace Sudoku.Infrastructure.Storage;

public sealed class ModelsRegistryGateway : IModelsRegistryGateway
{
    private static readonly JsonSerializerOptions JsonSerializerOptions = new(JsonSerializerDefaults.Web)
    {
        WriteIndented = true
    };

    private const string ManifestFileName = "model.json";
    private const string ArtifactsDirectoryName = "artifacts";
    private const string ArtifactMissingWarning = "model_artifacts_missing";
    private const string PrimaryArtifactMissingWarning = "primary_artifact_missing";

    private readonly IFileStorageGateway _fileStorageGateway;
    private readonly ModelsRegistryStorageOptions _modelsRegistryStorageOptions;

    public ModelsRegistryGateway(
        IFileStorageGateway fileStorageGateway,
        IOptions<ModelsRegistryStorageOptions> modelsRegistryStorageOptions)
    {
        _fileStorageGateway = fileStorageGateway;
        _modelsRegistryStorageOptions = modelsRegistryStorageOptions.Value;
    }

    public async Task<IReadOnlyList<RegistryModelManifestDto>> ListAsync(
        CancellationToken cancellationToken = default)
    {
        var directories = await _fileStorageGateway.ListDirectoriesAsync(
            _modelsRegistryStorageOptions.RegistryDirectoryPath,
            cancellationToken);

        var manifests = new List<RegistryModelManifestDto>(directories.Count);
        foreach (var directory in directories.OrderBy(item => item.Name, StringComparer.Ordinal))
        {
            cancellationToken.ThrowIfCancellationRequested();

            try
            {
                manifests.Add(await ReadManifestAsync(directory, cancellationToken));
            }
            catch (FileStorageItemNotFoundException)
            {
                continue;
            }
        }

        return manifests;
    }

    public async Task<RegistryModelManifestDto?> GetByNameAsync(
        string modelName,
        CancellationToken cancellationToken = default)
    {
        try
        {
            return await ReadManifestAsync(
                new StoredDirectoryMetadataDto(modelName, default),
                cancellationToken);
        }
        catch (FileStorageItemNotFoundException)
        {
            return null;
        }
    }

    public async Task FinalizeTrainedModelAsync(
        FinalizeTrainedModelManifestDto manifest,
        CancellationToken cancellationToken = default)
    {
        EnsureRelativePath(manifest.PrimaryArtifactRelativePath, "artifacts.primaryArtifactRelativePath");

        var entryDirectoryPath = Path.GetFullPath(Path.Combine(
            _modelsRegistryStorageOptions.RegistryDirectoryPath,
            manifest.Name));

        var artifactExists = await _fileStorageGateway.FileExistsAsync(
            entryDirectoryPath,
            manifest.PrimaryArtifactRelativePath,
            cancellationToken);

        if (!artifactExists)
        {
            throw new FileStorageItemNotFoundException("Główny artefakt modelu wynikowego nie jest jeszcze dostępny.");
        }

        var payload = new
        {
            name = manifest.Name,
            displayName = manifest.DisplayName,
            sourceType = "training",
            sourceRunName = manifest.SourceRunName,
            parentModelName = manifest.ParentModelName,
            trainingMode = manifest.TrainingMode,
            architecture = new
            {
                inputProfile = manifest.InputProfile
            },
            training = new
            {
                defaultTrainingProfileName = manifest.TrainingProfileName,
                defaultAugmentationProfileName = manifest.AugmentationProfileName
            },
            artifacts = new
            {
                primaryArtifactRelativePath = manifest.PrimaryArtifactRelativePath
            },
            capabilities = new
            {
                canStartTraining = true,
                canUseForInference = true
            },
            metadata = new
            {
                createdAtUtc = manifest.CreatedAtUtc
            }
        };

        var json = JsonSerializer.Serialize(payload, JsonSerializerOptions);
        await using var content = new MemoryStream(Encoding.UTF8.GetBytes(json));
        await _fileStorageGateway.ReplaceAsync(
            entryDirectoryPath,
            ManifestFileName,
            content,
            cancellationToken);
    }

    private async Task<RegistryModelManifestDto> ReadManifestAsync(
        StoredDirectoryMetadataDto directory,
        CancellationToken cancellationToken)
    {
        var entryDirectoryPath = Path.GetFullPath(Path.Combine(
            _modelsRegistryStorageOptions.RegistryDirectoryPath,
            directory.Name));

        await using var stream = await _fileStorageGateway.OpenReadAsync(
            entryDirectoryPath,
            ManifestFileName,
            cancellationToken);

        using var document = await JsonDocument.ParseAsync(stream, cancellationToken: cancellationToken);
        var root = document.RootElement;

        var name = GetRequiredString(root, "name");
        if (!string.Equals(name, directory.Name, StringComparison.Ordinal))
        {
            throw new InvalidDataException(
                $"Nazwa modelu {name} w manifeście nie odpowiada katalogowi rejestru {directory.Name}.");
        }

        var sourceType = GetRequiredString(root, "sourceType");
        var sourceRunName = GetNullableString(root, "sourceRunName");
        var canStartTraining = GetRequiredBoolean(root, "capabilities", "canStartTraining");
        var canUseForInference = GetRequiredBoolean(root, "capabilities", "canUseForInference");
        var primaryArtifactRelativePath = GetRequiredString(root, "artifacts", "primaryArtifactRelativePath");
        EnsureRelativePath(primaryArtifactRelativePath, "artifacts.primaryArtifactRelativePath");

        var warnings = await GetTechnicalWarningsAsync(
            entryDirectoryPath,
            primaryArtifactRelativePath,
            cancellationToken);

        if ((canStartTraining || canUseForInference) && warnings.Count > 0)
        {
            throw new InvalidDataException(
                $"Model {name} deklaruje capability wymagające kompletnych artefaktów, ale rejestr jest niekompletny.");
        }

        return new RegistryModelManifestDto(
            Name: name,
            DisplayName: GetNullableString(root, "displayName") ?? name,
            SourceType: sourceType,
            SourceRunName: sourceRunName,
            ParentModelName: GetNullableString(root, "parentModelName"),
            TrainingMode: GetNullableString(root, "trainingMode") ?? ResolveDefaultTrainingMode(sourceType),
            InputProfile: GetRequiredString(root, "architecture", "inputProfile"),
            TrainingProfileName: GetNullableString(root, "training", "defaultTrainingProfileName")
                ?? GetNullableString(root, "trainingProfileName"),
            AugmentationProfileName: GetNullableString(root, "training", "defaultAugmentationProfileName")
                ?? GetNullableString(root, "augmentationProfileName"),
            CreatedAtUtc: GetNullableDateTimeOffset(root, "createdAtUtc")
                ?? GetNullableDateTimeOffset(root, "metadata", "createdAtUtc"),
            CanStartTraining: canStartTraining,
            CanUseForInference: canUseForInference,
            PrimaryArtifactRelativePath: primaryArtifactRelativePath,
            Warnings: warnings);
    }

    private async Task<IReadOnlyList<string>> GetTechnicalWarningsAsync(
        string entryDirectoryPath,
        string primaryArtifactRelativePath,
        CancellationToken cancellationToken)
    {
        var warnings = new List<string>();
        var childDirectories = await _fileStorageGateway.ListDirectoriesAsync(
            entryDirectoryPath,
            cancellationToken);

        if (!childDirectories.Any(
                directory => string.Equals(directory.Name, ArtifactsDirectoryName, StringComparison.Ordinal)))
        {
            warnings.Add(ArtifactMissingWarning);
        }

        try
        {
            await using var artifactStream = await _fileStorageGateway.OpenReadAsync(
                entryDirectoryPath,
                primaryArtifactRelativePath,
                cancellationToken);
        }
        catch (FileStorageItemNotFoundException)
        {
            warnings.Add(PrimaryArtifactMissingWarning);
        }

        return warnings.Distinct(StringComparer.Ordinal).ToArray();
    }

    private static string ResolveDefaultTrainingMode(string sourceType)
    {
        return string.Equals(sourceType, "bootstrap", StringComparison.OrdinalIgnoreCase)
            ? "externalBaseline"
            : "fineTuning";
    }

    private static void EnsureRelativePath(string value, string fieldName)
    {
        if (string.IsNullOrWhiteSpace(value) || Path.IsPathRooted(value))
        {
            throw new InvalidDataException($"Pole {fieldName} musi być niepustą ścieżką względną.");
        }
    }

    private static string GetRequiredString(JsonElement root, params string[] path)
    {
        if (!TryGetProperty(root, out var property, path)
            || property.ValueKind != JsonValueKind.String
            || string.IsNullOrWhiteSpace(property.GetString()))
        {
            throw new InvalidDataException($"Manifest modelu nie zawiera wymaganego pola {string.Join('.', path)}.");
        }

        return property.GetString()!;
    }

    private static string? GetNullableString(JsonElement root, params string[] path)
    {
        if (!TryGetProperty(root, out var property, path) || property.ValueKind == JsonValueKind.Null)
        {
            return null;
        }

        if (property.ValueKind != JsonValueKind.String)
        {
            throw new InvalidDataException($"Pole {string.Join('.', path)} musi być tekstem albo null.");
        }

        return property.GetString();
    }

    private static bool GetRequiredBoolean(JsonElement root, params string[] path)
    {
        if (!TryGetProperty(root, out var property, path)
            || property.ValueKind is not JsonValueKind.True and not JsonValueKind.False)
        {
            throw new InvalidDataException($"Manifest modelu nie zawiera wymaganego pola boolean {string.Join('.', path)}.");
        }

        return property.GetBoolean();
    }

    private static DateTimeOffset? GetNullableDateTimeOffset(JsonElement root, params string[] path)
    {
        var value = GetNullableString(root, path);
        if (value is null)
        {
            return null;
        }

        return DateTimeOffset.TryParse(value, out var parsed)
            ? parsed
            : throw new InvalidDataException($"Pole {string.Join('.', path)} musi być datą w formacie ISO-8601.");
    }

    private static bool TryGetProperty(JsonElement root, out JsonElement property, params string[] path)
    {
        var current = root;
        foreach (var segment in path)
        {
            if (current.ValueKind != JsonValueKind.Object
                || !current.TryGetProperty(segment, out current))
            {
                property = default;
                return false;
            }
        }

        property = current;
        return true;
    }
}
