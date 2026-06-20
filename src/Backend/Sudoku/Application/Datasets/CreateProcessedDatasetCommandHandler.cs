using MediatR;
using Microsoft.Extensions.Options;
using Sudoku.Application.Abstractions;
using Sudoku.Application.Ml;
using Sudoku.Application.Storage;
using Sudoku.Models.Datasets;

namespace Sudoku.Application.Datasets;

public sealed class CreateProcessedDatasetCommandHandler
    : IRequestHandler<CreateProcessedDatasetCommand, CreateProcessedDatasetCommandResultDto>
{
    private readonly IDatasetPreparationsGateway _datasetPreparationsGateway;
    private readonly IDatasetPreparationArtifactsGateway _datasetPreparationArtifactsGateway;
    private readonly IMlDatasetsPreparationGateway _mlDatasetsPreparationGateway;
    private readonly IProcessedDatasetsGateway _processedDatasetsGateway;
    private readonly DatasetsPreparationOptions _datasetsPreparationOptions;
    private readonly TimeProvider _timeProvider;

    public CreateProcessedDatasetCommandHandler(
        IDatasetPreparationsGateway datasetPreparationsGateway,
        IDatasetPreparationArtifactsGateway datasetPreparationArtifactsGateway,
        IMlDatasetsPreparationGateway mlDatasetsPreparationGateway,
        IProcessedDatasetsGateway processedDatasetsGateway,
        IOptions<DatasetsPreparationOptions> datasetsPreparationOptions,
        TimeProvider timeProvider)
    {
        _datasetPreparationsGateway = datasetPreparationsGateway;
        _datasetPreparationArtifactsGateway = datasetPreparationArtifactsGateway;
        _mlDatasetsPreparationGateway = mlDatasetsPreparationGateway;
        _processedDatasetsGateway = processedDatasetsGateway;
        _datasetsPreparationOptions = datasetsPreparationOptions.Value;
        _timeProvider = timeProvider;
    }

    public async Task<CreateProcessedDatasetCommandResultDto> Handle(
        CreateProcessedDatasetCommand request,
        CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(request.PreparationName)
            || string.IsNullOrWhiteSpace(request.Name)
            || request.Sources is null
            || request.Sources.Count == 0)
        {
            throw new InvalidOperationException("CreateProcessedDatasetCommand must be validated before handler execution.");
        }

        var preparationName = request.PreparationName.Trim();
        var datasetName = request.Name.Trim();
        var targetFileName = $"{datasetName}.npz";

        var isNameAvailable = await _processedDatasetsGateway.IsProcessedDatasetNameAvailableAsync(
            datasetName,
            cancellationToken);

        if (!isNameAvailable)
        {
            throw new FileStorageConflictException($"Zestaw {targetFileName} już istnieje.");
        }

        var selectedSources = request.Sources
            .Select(source => new SelectedRawDatasetSourceDto(
                Name: source.Name.Trim(),
                Type: source.Type.Trim().ToLowerInvariant(),
                Splits: source.Splits
                    .Select(split => split.Trim().ToLowerInvariant())
                    .Distinct(StringComparer.Ordinal)
                    .ToArray()))
            .ToArray();

        await EnsurePreparationExistsAndIsCompletedAsync(preparationName, cancellationToken);
        await ValidateSelectedSourcesAgainstPreparationAsync(preparationName, selectedSources, cancellationToken);

        var prepareRequest = new PrepareDatasetArtifactRequestDto(
            PreparationName: preparationName,
            DatasetName: datasetName,
            SplitPolicy: BuildRequestSplitPolicy(),
            Sources: selectedSources
                .Select(source => new PrepareDatasetSourceDto(
                    Name: source.Name,
                    Type: source.Type,
                    Splits: source.Splits))
                .ToArray());

        var preparedArtifact = await _mlDatasetsPreparationGateway.PrepareDatasetArtifactAsync(
            prepareRequest,
            cancellationToken);

        if (SumSplitCounts(preparedArtifact.SampleCounts) == 0)
        {
            throw new NoSamplesPreparedException("Nie udało się przygotować żadnej poprawnej próbki datasetu.");
        }

        await _processedDatasetsGateway.PromotePreparedArtifactAsync(
            datasetName,
            targetFileName,
            cancellationToken);

        var createdAtUtc = _timeProvider.GetUtcNow();
        var result = new CreateProcessedDatasetCommandResultDto(
            Name: datasetName,
            FileName: targetFileName,
            PreprocessingProfile: _datasetsPreparationOptions.DefaultPreprocessingProfile,
            CreatedAtUtc: createdAtUtc,
            Sources: selectedSources,
            SampleCounts: preparedArtifact.SampleCounts,
            SourceReports: MapSourceReports(selectedSources, preparedArtifact),
            Warnings: preparedArtifact.Warnings);

        await _processedDatasetsGateway.SaveMetadataAsync(
            new ProcessedDatasetMetadataDto(
                Name: result.Name,
                PreparationName: preparationName,
                FileName: result.FileName,
                PreprocessingProfile: result.PreprocessingProfile,
                CreatedAtUtc: result.CreatedAtUtc,
                Sources: result.Sources,
                SampleCounts: result.SampleCounts,
                SourceReports: result.SourceReports,
                Warnings: result.Warnings),
            cancellationToken);

        return result;
    }

    private async Task EnsurePreparationExistsAndIsCompletedAsync(
        string preparationName,
        CancellationToken cancellationToken)
    {
        var preparation = await _datasetPreparationsGateway.GetByNameAsync(preparationName, cancellationToken);
        if (preparation is null)
        {
            throw new DatasetPreparationNotFoundException(preparationName);
        }

        if (!string.Equals(preparation.Status, DatasetPreparationStatus.Completed, StringComparison.OrdinalIgnoreCase))
        {
            throw new DatasetPreparationArtifactsNotReadyException(preparationName, preparation.Status);
        }
    }

    private async Task ValidateSelectedSourcesAgainstPreparationAsync(
        string preparationName,
        IReadOnlyList<SelectedRawDatasetSourceDto> selectedSources,
        CancellationToken cancellationToken)
    {
        var allowedBoardSources = await _datasetPreparationArtifactsGateway.GetSourceFolderNamesAsync(
            preparationName,
            "board",
            cancellationToken);
        var allowedDigitSources = await _datasetPreparationArtifactsGateway.GetSourceFolderNamesAsync(
            preparationName,
            "digit",
            cancellationToken);

        var allowedBoardSourcesSet = new HashSet<string>(allowedBoardSources, StringComparer.Ordinal);
        var allowedDigitSourcesSet = new HashSet<string>(allowedDigitSources, StringComparer.Ordinal);

        foreach (var source in selectedSources)
        {
            var allowedSources = string.Equals(source.Type, "board", StringComparison.Ordinal)
                ? allowedBoardSourcesSet
                : allowedDigitSourcesSet;

            if (!allowedSources.Contains(source.Name))
            {
                throw new DatasetPreparationSourceNotFoundException(preparationName, source.Name);
            }
        }
    }

    private DatasetSplitPolicyDto BuildRequestSplitPolicy()
    {
        return new DatasetSplitPolicyDto(
            Mode: "ratio",
            Ratios: new SplitRatiosDto(
                Train: _datasetsPreparationOptions.DefaultMixSplitRatios.Train,
                Val: _datasetsPreparationOptions.DefaultMixSplitRatios.Val,
                Test: _datasetsPreparationOptions.DefaultMixSplitRatios.Test),
            GroupBy: "sourceType");
    }

    private static int SumSplitCounts(SplitSampleCountsDto splitSampleCounts)
    {
        return splitSampleCounts.Train + splitSampleCounts.Val + splitSampleCounts.Test;
    }

    private static IReadOnlyList<ProcessedDatasetSourceReportDto> MapSourceReports(
        IReadOnlyList<SelectedRawDatasetSourceDto> selectedSources,
        PrepareDatasetArtifactResultDto preparedArtifact)
    {
        var reportsBySourceKey = preparedArtifact.Sources
            .GroupBy(
                report => CreateSourceKey(report.Name, report.RequestedType),
                StringComparer.Ordinal)
            .ToDictionary(group => group.Key, group => group.First(), StringComparer.Ordinal);

        return selectedSources
            .Select(source =>
            {
                if (!reportsBySourceKey.TryGetValue(CreateSourceKey(source.Name, source.Type), out var report))
                {
                    throw new MlOperationFailedException(
                        CreateProcessedDatasetErrorTypes.DatasetSourceInvalid,
                        $"Serwis ML nie zwrócił raportu dla źródła {source.Name}.");
                }

                return new ProcessedDatasetSourceReportDto(
                    Name: source.Name,
                    Type: source.Type,
                    ProcessedSampleCount: report.ProcessedSampleCount,
                    IncludedSampleCount: report.IncludedSampleCount,
                    EmptyCellCount: report.EmptyCellCount,
                    RejectedSampleCount: report.RejectedSampleCount,
                    Warnings: report.Warnings);
            })
            .ToArray();
    }

    private static string CreateSourceKey(string name, string type)
    {
        return $"{name}::{type.ToLowerInvariant()}";
    }
}
