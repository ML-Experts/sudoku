using MediatR;
using Sudoku.Application.Abstractions;

namespace Sudoku.Application.Trainings;

public sealed class ListTrainingRunsQueryHandler
    : IRequestHandler<ListTrainingRunsQuery, ListTrainingRunsQueryResultDto>
{
    private readonly ITrainingRunsGateway _trainingRunsGateway;

    public ListTrainingRunsQueryHandler(ITrainingRunsGateway trainingRunsGateway)
    {
        _trainingRunsGateway = trainingRunsGateway;
    }

    public async Task<ListTrainingRunsQueryResultDto> Handle(
        ListTrainingRunsQuery request,
        CancellationToken cancellationToken)
    {
        var metadataItems = await _trainingRunsGateway.ListAsync(cancellationToken);

        EnsureNoDuplicateRunNames(metadataItems);

        var items = metadataItems
            .Select(ToListItem)
            .OrderByDescending(item => item.CreatedAtUtc)
            .ThenBy(item => item.RunName, StringComparer.Ordinal)
            .ToArray();

        return new ListTrainingRunsQueryResultDto(
            Items: items,
            TotalCount: items.Length);
    }

    private static TrainingRunListItemDto ToListItem(TrainingRunMetadataDto metadata)
    {
        EnsureListableMetadata(metadata);

        return new TrainingRunListItemDto(
            RunName: metadata.RunName,
            Status: metadata.Status,
            CreatedAtUtc: metadata.CreatedAtUtc,
            UpdatedAtUtc: metadata.UpdatedAtUtc,
            StartedAtUtc: metadata.StartedAtUtc,
            FinishedAtUtc: metadata.FinishedAtUtc,
            BaseModelName: metadata.BaseModelName,
            ProducedModelName: metadata.ProducedModelName,
            ProcessedDatasetName: metadata.ProcessedDatasetName,
            TrainingMode: metadata.TrainingMode,
            TrainingProfileName: metadata.TrainingProfileName,
            AugmentationProfileName: metadata.AugmentationProfileName,
            BenchmarkName: metadata.BenchmarkName,
            ReportStatus: metadata.ReportStatus,
            Progress: metadata.Progress,
            MetricsSummary: metadata.MetricsSummary,
            Warnings: metadata.Warnings ?? Array.Empty<string>());
    }

    private static void EnsureNoDuplicateRunNames(IReadOnlyList<TrainingRunMetadataDto> metadataItems)
    {
        var duplicateRunName = metadataItems
            .Where(metadata => !string.IsNullOrWhiteSpace(metadata.RunName))
            .GroupBy(metadata => metadata.RunName, StringComparer.Ordinal)
            .Where(group => group.Count() > 1)
            .Select(group => group.Key)
            .FirstOrDefault();

        if (duplicateRunName is not null)
        {
            throw new InvalidDataException(
                $"Wykryto zduplikowany runName w metadanych treningów: {duplicateRunName}.");
        }
    }

    private static void EnsureListableMetadata(TrainingRunMetadataDto metadata)
    {
        EnsureRequired(metadata.RunName, nameof(metadata.RunName));
        EnsureRequired(metadata.Status, nameof(metadata.Status));
        EnsureRequired(metadata.BaseModelName, nameof(metadata.BaseModelName));
        EnsureRequired(metadata.ProducedModelName, nameof(metadata.ProducedModelName));
        EnsureRequired(metadata.ProcessedDatasetName, nameof(metadata.ProcessedDatasetName));
        EnsureRequired(metadata.TrainingMode, nameof(metadata.TrainingMode));
        EnsureRequired(metadata.TrainingProfileName, nameof(metadata.TrainingProfileName));
        EnsureRequired(metadata.AugmentationProfileName, nameof(metadata.AugmentationProfileName));
        EnsureRequired(metadata.BenchmarkName, nameof(metadata.BenchmarkName));

        if (metadata.CreatedAtUtc == default)
        {
            throw new InvalidDataException(
                $"Metadane runu treningowego {metadata.RunName} nie zawierają poprawnego {nameof(metadata.CreatedAtUtc)}.");
        }
    }

    private static void EnsureRequired(string? value, string fieldName)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            throw new InvalidDataException(
                $"Metadane runu treningowego nie zawierają wymaganego pola {fieldName}.");
        }
    }
}
