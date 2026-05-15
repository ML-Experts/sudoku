using System.Text.Json;
using Microsoft.Extensions.Options;
using Sudoku.Application.Abstractions;
using Sudoku.Application.ModelsRegistry;

namespace Sudoku.Application.ModelsActive;

public sealed class ActiveModelResolver : IActiveModelResolver
{
    private readonly IActiveModelPointerGateway _activeModelPointerGateway;
    private readonly IModelsRegistryGateway _modelsRegistryGateway;
    private readonly ModelsRegistryStorageOptions _modelsRegistryStorageOptions;

    public ActiveModelResolver(
        IActiveModelPointerGateway activeModelPointerGateway,
        IModelsRegistryGateway modelsRegistryGateway,
        IOptions<ModelsRegistryStorageOptions> modelsRegistryStorageOptions)
    {
        _activeModelPointerGateway = activeModelPointerGateway;
        _modelsRegistryGateway = modelsRegistryGateway;
        _modelsRegistryStorageOptions = modelsRegistryStorageOptions.Value;
    }

    public async Task<ResolvedActiveModelDto?> ResolveForInferenceAsync(
        CancellationToken cancellationToken = default)
    {
        var pointer = await ResolvePointerAsync(cancellationToken);
        if (pointer is null)
        {
            return null;
        }

        var modelName = ResolvePointerModelName(pointer);
        var manifest = await ResolveManifestAsync(modelName, cancellationToken);
        ActiveModelActivationRules.EnsureCanUseForInference(manifest);
        ActiveModelActivationRules.EnsureActivatableManifest(manifest);

        var modelDirectoryPath = Path.GetFullPath(Path.Combine(
            _modelsRegistryStorageOptions.RegistryDirectoryPath,
            manifest.Name));
        var manifestPath = Path.Combine(modelDirectoryPath, "model.json");
        var primaryArtifactPath = Path.GetFullPath(Path.Combine(
            modelDirectoryPath,
            manifest.PrimaryArtifactRelativePath!));

        return new ResolvedActiveModelDto(
            Pointer: pointer,
            Manifest: manifest,
            ManifestPath: manifestPath,
            PrimaryArtifactPath: primaryArtifactPath);
    }

    private async Task<ActiveModelPointerDto?> ResolvePointerAsync(CancellationToken cancellationToken)
    {
        try
        {
            return await _activeModelPointerGateway.GetAsync(cancellationToken);
        }
        catch (JsonException exception)
        {
            throw new ActiveModelPointerInvalidException(
                modelName: null,
                "Wskaźnik aktywnego modelu jest uszkodzony albo ma niepoprawny format.",
                exception);
        }
        catch (Exception exception) when (exception is IOException
                                         or UnauthorizedAccessException
                                         or InvalidOperationException)
        {
            throw new ActiveModelPointerReadException(
                "Nie udało się odczytać wskaźnika aktywnego modelu.",
                exception);
        }
    }

    private static string ResolvePointerModelName(ActiveModelPointerDto pointer)
    {
        var failure = ActiveModelActivationRules.ValidateModelName(
            pointer.ModelName,
            nameof(ActiveModelPointerDto.ModelName));
        if (failure is not null)
        {
            throw new ActiveModelPointerInvalidException(
                pointer.ModelName,
                "Wskaźnik aktywnego modelu zawiera niepoprawną nazwę modelu.");
        }

        if (pointer.UpdatedAtUtc == default)
        {
            throw new ActiveModelPointerInvalidException(
                pointer.ModelName,
                "Wskaźnik aktywnego modelu nie zawiera poprawnej daty aktualizacji.");
        }

        return pointer.ModelName.Trim();
    }

    private async Task<RegistryModelManifestDto> ResolveManifestAsync(
        string modelName,
        CancellationToken cancellationToken)
    {
        try
        {
            var manifest = await _modelsRegistryGateway.GetByNameAsync(modelName, cancellationToken);
            return manifest ?? throw new ActiveModelNotFoundException(modelName);
        }
        catch (Exception exception) when (exception is InvalidDataException
                                         or InvalidOperationException
                                         or JsonException)
        {
            throw new ActiveModelManifestInvalidException(
                modelName,
                $"Manifest modelu {modelName} jest niekompletny albo niepoprawny.",
                exception);
        }
    }
}
