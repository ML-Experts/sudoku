using MediatR;
using Sudoku.Application.Abstractions;

namespace Sudoku.Application.ModelsRegistry;

public sealed class ListRegistryModelsQueryHandler
    : IRequestHandler<ListRegistryModelsQuery, ListRegistryModelsQueryResultDto>
{
    private readonly IModelsRegistryGateway _modelsRegistryGateway;

    public ListRegistryModelsQueryHandler(IModelsRegistryGateway modelsRegistryGateway)
    {
        _modelsRegistryGateway = modelsRegistryGateway;
    }

    public async Task<ListRegistryModelsQueryResultDto> Handle(
        ListRegistryModelsQuery request,
        CancellationToken cancellationToken)
    {
        var manifests = await _modelsRegistryGateway.ListAsync(cancellationToken);
        EnsureNoDuplicateNames(manifests);

        var items = manifests
            .OrderByDescending(item => item.CreatedAtUtc ?? DateTimeOffset.MinValue)
            .ThenBy(item => item.Name, StringComparer.Ordinal)
            .Select(item => new RegistryModelListItemDto(
                Name: item.Name,
                DisplayName: item.DisplayName,
                SourceType: item.SourceType,
                SourceRunName: item.SourceRunName,
                ParentModelName: item.ParentModelName,
                TrainingMode: item.TrainingMode,
                InputProfile: item.InputProfile,
                TrainingProfileName: item.TrainingProfileName,
                AugmentationProfileName: item.AugmentationProfileName,
                CreatedAtUtc: item.CreatedAtUtc,
                CanStartTraining: item.CanStartTraining,
                CanUseForInference: item.CanUseForInference,
                Warnings: item.Warnings))
            .ToArray();

        return new ListRegistryModelsQueryResultDto(
            Items: items,
            TotalCount: items.Length);
    }

    private static void EnsureNoDuplicateNames(IReadOnlyList<RegistryModelManifestDto> manifests)
    {
        var duplicatedName = manifests
            .GroupBy(item => item.Name, StringComparer.Ordinal)
            .FirstOrDefault(group => group.Count() > 1)
            ?.Key;

        if (duplicatedName is not null)
        {
            throw new InvalidDataException(
                $"Rejestr modeli zawiera zduplikowaną nazwę modelu {duplicatedName}.");
        }
    }
}
