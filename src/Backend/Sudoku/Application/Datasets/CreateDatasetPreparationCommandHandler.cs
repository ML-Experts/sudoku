using MediatR;
using Sudoku.Application.Abstractions;
using Sudoku.Application.Storage;
using Sudoku.Models.Datasets;

namespace Sudoku.Application.Datasets;

public sealed class CreateDatasetPreparationCommandHandler
    : IRequestHandler<CreateDatasetPreparationCommand, CreateDatasetPreparationCommandResultDto>
{
    private readonly ISender _sender;
    private readonly IDatasetPreparationsGateway _datasetPreparationsGateway;
    private readonly IDatasetPreparationExecutionScheduler _executionScheduler;
    private readonly TimeProvider _timeProvider;

    public CreateDatasetPreparationCommandHandler(
        ISender sender,
        IDatasetPreparationsGateway datasetPreparationsGateway,
        IDatasetPreparationExecutionScheduler executionScheduler,
        TimeProvider timeProvider)
    {
        _sender = sender;
        _datasetPreparationsGateway = datasetPreparationsGateway;
        _executionScheduler = executionScheduler;
        _timeProvider = timeProvider;
    }

    public async Task<CreateDatasetPreparationCommandResultDto> Handle(
        CreateDatasetPreparationCommand request,
        CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(request.PreparationName)
            || request.Sources is null
            || request.Sources.Count == 0)
        {
            throw new InvalidOperationException("CreateDatasetPreparationCommand must be validated before handler execution.");
        }

        var preparationName = request.PreparationName.Trim();
        var selectedSources = request.Sources
            .Select(source => new CreateDatasetPreparationSourceDto(
                Name: source.Name.Trim(),
                Type: source.Type.Trim().ToLowerInvariant()))
            .ToArray();
        await ValidateSelectedSourcesAgainstRawCandidatesAsync(selectedSources, cancellationToken);

        var queuedMetadata = BuildQueuedMetadata(preparationName, selectedSources);
        var created = await _datasetPreparationsGateway.TryCreateAsync(queuedMetadata, cancellationToken);
        if (!created)
        {
            throw new FileStorageConflictException($"Przygotowanie {preparationName} już istnieje.");
        }

        await _executionScheduler.ScheduleAsync(new DatasetPreparationWorkItemDto(preparationName), cancellationToken);

        return new CreateDatasetPreparationCommandResultDto(
            PreparationName: queuedMetadata.PreparationName,
            CreatedAtUtc: queuedMetadata.CreatedAtUtc,
            Status: queuedMetadata.Status,
            Sources: queuedMetadata.SourceReports,
            Warnings: queuedMetadata.Warnings);
    }

    private async Task ValidateSelectedSourcesAgainstRawCandidatesAsync(
        IReadOnlyList<CreateDatasetPreparationSourceDto> selectedSources,
        CancellationToken cancellationToken)
    {
        var candidates = await _sender.Send(new ListRawDatasetCandidatesQuery(), cancellationToken);
        var candidatesByName = candidates.Items
            .GroupBy(item => item.Name, StringComparer.Ordinal)
            .ToDictionary(group => group.Key, group => group.ToArray(), StringComparer.Ordinal);

        foreach (var source in selectedSources)
        {
            if (!candidatesByName.TryGetValue(source.Name, out var variants))
            {
                throw new RawDatasetNotFoundException($"Źródło {source.Name} nie zostało odnalezione.");
            }

            var matchingVariant = variants.FirstOrDefault(item =>
                string.Equals(item.Type, source.Type, StringComparison.OrdinalIgnoreCase));
            if (matchingVariant is null)
            {
                throw new RawDatasetTypeMismatchException(
                    $"Źródło {source.Name} zostało wykryte jako {variants[0].Type} i nie może być przygotowane jako {source.Type}.");
            }
        }
    }

    private DatasetPreparationMetadataDto BuildQueuedMetadata(
        string preparationName,
        IReadOnlyList<CreateDatasetPreparationSourceDto> selectedSources)
    {
        var createdAtUtc = _timeProvider.GetUtcNow();
        return new DatasetPreparationMetadataDto(
            PreparationName: preparationName,
            Status: DatasetPreparationStatus.Queued,
            CreatedAtUtc: createdAtUtc,
            UpdatedAtUtc: createdAtUtc,
            StartedAtUtc: null,
            FinishedAtUtc: null,
            Sources: selectedSources,
            SourceReports: selectedSources
                .Select(source => new DatasetPreparationSourceReportDto(
                    Name: source.Name,
                    Type: source.Type,
                    PreparedItemsCount: 0,
                    RejectedItemsCount: 0,
                    EmptyCellCount: 0))
                .ToArray(),
            Warnings: Array.Empty<string>(),
            FailureErrorType: null,
            FailureMessage: null);
    }
}
