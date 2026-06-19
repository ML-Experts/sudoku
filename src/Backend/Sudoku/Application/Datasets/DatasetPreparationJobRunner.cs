using Sudoku.Application.Abstractions;
using Sudoku.Application.Ml;
using Sudoku.Models.Datasets;

namespace Sudoku.Application.Datasets;

public sealed class DatasetPreparationJobRunner
{
    private readonly IDatasetPreparationsGateway _datasetPreparationsGateway;
    private readonly IMlDatasetPreparationsGateway _mlDatasetPreparationsGateway;
    private readonly TimeProvider _timeProvider;

    public DatasetPreparationJobRunner(
        IDatasetPreparationsGateway datasetPreparationsGateway,
        IMlDatasetPreparationsGateway mlDatasetPreparationsGateway,
        TimeProvider timeProvider)
    {
        _datasetPreparationsGateway = datasetPreparationsGateway;
        _mlDatasetPreparationsGateway = mlDatasetPreparationsGateway;
        _timeProvider = timeProvider;
    }

    public async Task RunAsync(string preparationName, CancellationToken cancellationToken)
    {
        var metadata = await _datasetPreparationsGateway.GetByNameAsync(preparationName, cancellationToken);
        if (metadata is null)
        {
            return;
        }

        if (DatasetPreparationStatus.IsTerminal(metadata.Status))
        {
            return;
        }

        var runningMetadata = await MarkRunningAsync(metadata, cancellationToken);

        try
        {
            var mlResult = await CreatePreparationWithMlAsync(runningMetadata, cancellationToken);
            var completedMetadata = BuildCompletedMetadata(runningMetadata, mlResult);
            await _datasetPreparationsGateway.UpdateAsync(completedMetadata, cancellationToken);
        }
        catch (OperationCanceledException) when (cancellationToken.IsCancellationRequested)
        {
            throw;
        }
        catch (Exception exception)
        {
            await MarkFailedAsync(runningMetadata, exception, cancellationToken);
        }
    }

    private async Task<DatasetPreparationMetadataDto> MarkRunningAsync(
        DatasetPreparationMetadataDto metadata,
        CancellationToken cancellationToken)
    {
        var startedAtUtc = metadata.StartedAtUtc ?? _timeProvider.GetUtcNow();
        var runningMetadata = metadata with
        {
            Status = DatasetPreparationStatus.Running,
            UpdatedAtUtc = startedAtUtc,
            StartedAtUtc = startedAtUtc,
            FinishedAtUtc = null,
            FailureErrorType = null,
            FailureMessage = null
        };

        await _datasetPreparationsGateway.UpdateAsync(runningMetadata, cancellationToken);

        return runningMetadata;
    }

    private Task<CreateDatasetPreparationMlResultDto> CreatePreparationWithMlAsync(
        DatasetPreparationMetadataDto metadata,
        CancellationToken cancellationToken)
    {
        var request = new CreateDatasetPreparationMlRequestDto(
            PreparationName: metadata.PreparationName,
            Sources: metadata.Sources
                .Select(source => new CreateDatasetPreparationMlSourceDto(
                    Name: source.Name,
                    Type: source.Type))
                .ToArray());

        return _mlDatasetPreparationsGateway.CreateAsync(request, cancellationToken);
    }

    private DatasetPreparationMetadataDto BuildCompletedMetadata(
        DatasetPreparationMetadataDto runningMetadata,
        CreateDatasetPreparationMlResultDto mlResult)
    {
        var completedAtUtc = _timeProvider.GetUtcNow();
        var warnings = MergeWarnings(
            runningMetadata.Warnings,
            mlResult.Warnings,
            BuildMlConsistencyWarnings(runningMetadata, mlResult));

        return runningMetadata with
        {
            Status = DatasetPreparationStatus.Completed,
            UpdatedAtUtc = completedAtUtc,
            FinishedAtUtc = completedAtUtc,
            SourceReports = MapSourceReportsByNameAndType(runningMetadata.Sources, mlResult.SourceReports),
            Warnings = warnings,
            FailureErrorType = null,
            FailureMessage = null
        };
    }

    private async Task MarkFailedAsync(
        DatasetPreparationMetadataDto runningMetadata,
        Exception exception,
        CancellationToken cancellationToken)
    {
        var warnings = new List<string>();

        try
        {
            await CleanupGeneratedContentBestEffortAsync(runningMetadata.PreparationName, cancellationToken);
        }
        catch (Exception cleanupException)
        {
            warnings.Add(CreateDatasetPreparationErrorTypes.PreparationCleanupPartial);
            _ = cleanupException;
        }

        var failedAtUtc = _timeProvider.GetUtcNow();
        var failureErrorType = MapFailureErrorType(exception);
        var failedMetadata = runningMetadata with
        {
            Status = DatasetPreparationStatus.Failed,
            UpdatedAtUtc = failedAtUtc,
            FinishedAtUtc = failedAtUtc,
            FailureErrorType = failureErrorType,
            FailureMessage = exception.Message,
            Warnings = MergeWarnings(runningMetadata.Warnings, warnings)
        };

        await _datasetPreparationsGateway.UpdateAsync(failedMetadata, cancellationToken);
    }

    private Task CleanupGeneratedContentBestEffortAsync(
        string preparationName,
        CancellationToken cancellationToken)
    {
        return _datasetPreparationsGateway.CleanupGeneratedContentAsync(preparationName, cancellationToken);
    }

    private static IReadOnlyList<DatasetPreparationSourceReportDto> MapSourceReportsByNameAndType(
        IReadOnlyList<CreateDatasetPreparationSourceDto> selectedSources,
        IReadOnlyList<DatasetPreparationMlSourceReportDto> mlReports)
    {
        var reportsByKey = mlReports
            .GroupBy(report => CreateSourceKey(report.Name, report.Type), StringComparer.Ordinal)
            .ToDictionary(group => group.Key, group => group.Single(), StringComparer.Ordinal);

        return selectedSources
            .Select(source =>
            {
                if (!reportsByKey.TryGetValue(CreateSourceKey(source.Name, source.Type), out var report))
                {
                    throw new MlOperationFailedException(
                        CreateDatasetPreparationErrorTypes.PreparationInvariantViolation,
                        $"Serwis ML nie zwrócił raportu dla źródła {source.Name}.");
                }

                return new DatasetPreparationSourceReportDto(
                    Name: source.Name,
                    Type: source.Type,
                    PreparedItemsCount: report.PreparedItemsCount,
                    RejectedItemsCount: report.RejectedItemsCount,
                    EmptyCellCount: report.EmptyCellCount);
            })
            .ToArray();
    }

    private static IReadOnlyList<string> BuildMlConsistencyWarnings(
        DatasetPreparationMetadataDto metadata,
        CreateDatasetPreparationMlResultDto mlResult)
    {
        var warnings = new List<string>();
        if (!string.IsNullOrWhiteSpace(mlResult.PreparationName)
            && !string.Equals(mlResult.PreparationName, metadata.PreparationName, StringComparison.Ordinal))
        {
            warnings.Add("ml_preparation_name_mismatch");
        }

        if (!string.IsNullOrWhiteSpace(mlResult.Status)
            && !string.Equals(mlResult.Status, DatasetPreparationStatus.Completed, StringComparison.OrdinalIgnoreCase))
        {
            warnings.Add("ml_preparation_status_mismatch");
        }

        return warnings;
    }

    private static IReadOnlyList<string> MergeWarnings(params IReadOnlyList<string>?[] warningSets)
    {
        return warningSets
            .SelectMany(static warnings => warnings ?? Array.Empty<string>())
            .Where(warning => !string.IsNullOrWhiteSpace(warning))
            .Select(warning => warning.Trim())
            .Distinct(StringComparer.Ordinal)
            .ToArray();
    }

    private static string MapFailureErrorType(Exception exception)
    {
        return exception switch
        {
            MlServiceUnavailableException => CreateDatasetPreparationErrorTypes.MlUnavailable,
            MlServiceTimeoutException => CreateDatasetPreparationErrorTypes.MlTimeout,
            MlOperationFailedException mlOperationFailedException
                when !string.IsNullOrWhiteSpace(mlOperationFailedException.ErrorType)
                => mlOperationFailedException.ErrorType,
            InvalidDataException => CreateDatasetPreparationErrorTypes.PreparationInvariantViolation,
            InvalidOperationException => CreateDatasetPreparationErrorTypes.PreparationInvariantViolation,
            _ => CreateDatasetPreparationErrorTypes.PreparationFailed
        };
    }

    private static string CreateSourceKey(string name, string type)
    {
        return $"{name}::{type.ToLowerInvariant()}";
    }
}
