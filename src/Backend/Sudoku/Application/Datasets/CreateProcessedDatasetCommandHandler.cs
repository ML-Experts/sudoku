using MediatR;
using Microsoft.Extensions.Options;
using Sudoku.Application.Abstractions;
using Sudoku.Application.Ml;
using Sudoku.Application.Storage;

namespace Sudoku.Application.Datasets;

public sealed class CreateProcessedDatasetCommandHandler
    : IRequestHandler<CreateProcessedDatasetCommand, CreateProcessedDatasetCommandResultDto>
{
    private static readonly string[] SelectedSplitsOrder = ["train", "val", "test"];

    private readonly ISender _sender;
    private readonly IMlDatasetsPreparationGateway _mlDatasetsPreparationGateway;
    private readonly IProcessedDatasetsGateway _processedDatasetsGateway;
    private readonly DatasetsPreparationOptions _datasetsPreparationOptions;
    private readonly TimeProvider _timeProvider;

    public CreateProcessedDatasetCommandHandler(
        ISender sender,
        IMlDatasetsPreparationGateway mlDatasetsPreparationGateway,
        IProcessedDatasetsGateway processedDatasetsGateway,
        IOptions<DatasetsPreparationOptions> datasetsPreparationOptions,
        TimeProvider timeProvider)
    {
        _sender = sender;
        _mlDatasetsPreparationGateway = mlDatasetsPreparationGateway;
        _processedDatasetsGateway = processedDatasetsGateway;
        _datasetsPreparationOptions = datasetsPreparationOptions.Value;
        _timeProvider = timeProvider;
    }

    public async Task<CreateProcessedDatasetCommandResultDto> Handle(
        CreateProcessedDatasetCommand request,
        CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(request.Name) || request.Sources is null || request.Sources.Count == 0)
        {
            throw new InvalidOperationException("CreateProcessedDatasetCommand must be validated before handler execution.");
        }

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

        await ValidateSelectedSourcesAgainstRawCandidatesAsync(selectedSources, cancellationToken);

        var prepareRequest = new PrepareDatasetArtifactRequestDto(
            DatasetName: datasetName,
            Sources: selectedSources
                .Select(source => new PrepareDatasetSourceDto(
                    Name: source.Name,
                    Type: source.Type,
                    SplitPolicy: BuildSplitPolicy(source)))
                .ToArray(),
            PreprocessingProfile: _datasetsPreparationOptions.DefaultPreprocessingProfile);

        PrepareDatasetArtifactResultDto preparedArtifact;
        try
        {
            preparedArtifact = await _mlDatasetsPreparationGateway.PrepareDatasetArtifactAsync(prepareRequest, cancellationToken);
        }
        catch (MlOperationFailedException exception)
            when (string.Equals(exception.ErrorType, CreateProcessedDatasetErrorTypes.InvalidRequest, StringComparison.Ordinal))
        {
            throw new MlOperationFailedException(CreateProcessedDatasetErrorTypes.DatasetSourceInvalid, exception.Message);
        }

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

    private async Task ValidateSelectedSourcesAgainstRawCandidatesAsync(
        IReadOnlyList<SelectedRawDatasetSourceDto> selectedSources,
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
                var detectedType = variants[0].Type;
                throw new RawDatasetTypeMismatchException(
                    $"Źródło {source.Name} zostało wykryte jako {detectedType} i nie może być przygotowane jako {source.Type}.");
            }
        }
    }

    private DatasetSplitPolicyDto BuildSplitPolicy(SelectedRawDatasetSourceDto source)
    {
        var hasMix = source.Splits.Contains("mix", StringComparer.Ordinal);
        var groupBy = string.Equals(source.Type, "board", StringComparison.OrdinalIgnoreCase)
            ? "board"
            : "sample";

        if (hasMix)
        {
            return new DatasetSplitPolicyDto(
                Mode: "mix",
                Ratios: new SplitRatiosDto(
                    Train: _datasetsPreparationOptions.DefaultMixSplitRatios.Train,
                    Val: _datasetsPreparationOptions.DefaultMixSplitRatios.Val,
                    Test: _datasetsPreparationOptions.DefaultMixSplitRatios.Test),
                GroupBy: groupBy);
        }

        var selectedSplits = SelectedSplitsOrder
            .Where(split => source.Splits.Contains(split, StringComparer.Ordinal))
            .ToArray();
        var ratioPerSplit = 1d / selectedSplits.Length;

        var ratios = new SplitRatiosDto(
            Train: selectedSplits.Contains("train", StringComparer.Ordinal) ? ratioPerSplit : 0d,
            Val: selectedSplits.Contains("val", StringComparer.Ordinal) ? ratioPerSplit : 0d,
            Test: selectedSplits.Contains("test", StringComparer.Ordinal) ? ratioPerSplit : 0d);

        return new DatasetSplitPolicyDto(
            Mode: "selected",
            Ratios: ratios,
            GroupBy: groupBy);
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
