using Sudoku.Application.Storage;
using Sudoku.Models.Sudoku;

namespace Sudoku.Application.SudokuSolve;

public sealed class SudokuSolveSessionRunner : ISudokuSolveSessionRunner
{
    private readonly ISolveSessionsGateway _solveSessionsGateway;
    private readonly ISudokuBacktrackingSolver _sudokuBacktrackingSolver;
    private readonly ISudokuSolveEventPublisher _sudokuSolveEventPublisher;
    private readonly ISolveSessionLockProvider _solveSessionLockProvider;
    private readonly TimeProvider _timeProvider;

    public SudokuSolveSessionRunner(
        ISolveSessionsGateway solveSessionsGateway,
        ISudokuBacktrackingSolver sudokuSolveBacktrackingSolver,
        ISudokuSolveEventPublisher sudokuSolveEventPublisher,
        ISolveSessionLockProvider solveSessionLockProvider,
        TimeProvider timeProvider)
    {
        _solveSessionsGateway = solveSessionsGateway;
        _sudokuBacktrackingSolver = sudokuSolveBacktrackingSolver;
        _sudokuSolveEventPublisher = sudokuSolveEventPublisher;
        _solveSessionLockProvider = solveSessionLockProvider;
        _timeProvider = timeProvider;
    }

    public async Task RunAsync(
        SolveSessionWorkItemDto workItem,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(workItem.SolveSessionId))
        {
            throw new InvalidOperationException("SolveSessionWorkItemDto must contain solveSessionId.");
        }

        SolveSessionMetadataDto? metadata = null;

        try
        {
            metadata = await PrepareForExecutionAsync(workItem.SolveSessionId, cancellationToken);
            if (metadata is null || SudokuSolveSessionStatus.IsTerminal(metadata.Status))
            {
                return;
            }

            var grid = new SudokuGrid(metadata.CurrentGrid);
            var sequence = metadata.LastAcceptedSequence ?? 0L;

            var solveResult = await _sudokuBacktrackingSolver.SolveAsync(
                grid,
                async (step, stepCancellationToken) =>
                {
                    await ApplyInterStepDelayIfNeededAsync(metadata, sequence, stepCancellationToken);
                    sequence++;
                    metadata = await PersistProgressAsync(
                        metadata,
                        step,
                        sequence,
                        stepCancellationToken);
                },
                cancellationToken);

            metadata = await FinalizeSolveAsync(metadata, grid.ToJaggedArray(), solveResult, cancellationToken);
        }
        catch (OperationCanceledException) when (cancellationToken.IsCancellationRequested)
        {
            if (metadata is not null)
            {
                await TryFinalizeTechnicalFailureAsync(
                    metadata.SolveSessionId,
                    status: SudokuSolveSessionStatus.Cancelled,
                    errorType: null,
                    message: null);
            }
        }
        catch (Exception)
        {
            if (metadata is not null)
            {
                await TryFinalizeTechnicalFailureAsync(
                    metadata.SolveSessionId,
                    status: SudokuSolveSessionStatus.Failed,
                    errorType: SolveSudokuErrorTypes.SolveExecutionFailed,
                    message: "Nie udało się wykonać sesji rozwiązywania sudoku.");
            }
        }
    }

    private async Task<SolveSessionMetadataDto?> PrepareForExecutionAsync(
        string solveSessionId,
        CancellationToken cancellationToken)
    {
        await using var solveSessionLock = await _solveSessionLockProvider.AcquireAsync(
            solveSessionId,
            cancellationToken);

        var latestMetadata = await _solveSessionsGateway.GetBySolveSessionIdAsync(solveSessionId, cancellationToken);
        if (latestMetadata is null || SudokuSolveSessionStatus.IsTerminal(latestMetadata.Status))
        {
            return latestMetadata;
        }

        var nowUtc = _timeProvider.GetUtcNow();
        if (string.Equals(latestMetadata.Status, SudokuSolveSessionStatus.Cancelling, StringComparison.OrdinalIgnoreCase)
            || cancellationToken.IsCancellationRequested)
        {
            var cancelledMetadata = SolveSessionStateTransitions.ToCancelled(latestMetadata, nowUtc);
            await SaveAndPublishLockedAsync(cancelledMetadata, cancellationToken);
            return cancelledMetadata;
        }

        var runningMetadata = SolveSessionStateTransitions.ToRunning(latestMetadata, nowUtc);
        await SaveAndPublishLockedAsync(runningMetadata, cancellationToken);

        return runningMetadata;
    }

    private async Task<SolveSessionMetadataDto> PersistProgressAsync(
        SolveSessionMetadataDto metadata,
        SudokuSolverStepDto step,
        long sequence,
        CancellationToken cancellationToken)
    {
        await using var solveSessionLock = await _solveSessionLockProvider.AcquireAsync(
            metadata.SolveSessionId,
            cancellationToken);

        var latestMetadata = await _solveSessionsGateway.GetBySolveSessionIdAsync(
            metadata.SolveSessionId,
            cancellationToken);
        if (latestMetadata is null
            || SudokuSolveSessionStatus.IsTerminal(latestMetadata.Status)
            || string.Equals(latestMetadata.Status, SudokuSolveSessionStatus.Cancelling, StringComparison.OrdinalIgnoreCase)
            || cancellationToken.IsCancellationRequested)
        {
            return latestMetadata ?? metadata;
        }

        var nextMetadata = latestMetadata with
        {
            CurrentGrid = CopyGrid(step.CurrentGrid),
            UpdatedAtUtc = _timeProvider.GetUtcNow(),
            LastAcceptedSequence = sequence,
            LastEventType = step.EventType,
            FailureErrorType = null,
            FailureMessage = null
        };

        await SaveAndPublishLockedAsync(nextMetadata, cancellationToken);
        return nextMetadata;
    }

    private async Task<SolveSessionMetadataDto> FinalizeSolveAsync(
        SolveSessionMetadataDto metadata,
        int?[][] finalGrid,
        SudokuBacktrackingSolveResultDto solveResult,
        CancellationToken cancellationToken)
    {
        await using var solveSessionLock = await _solveSessionLockProvider.AcquireAsync(
            metadata.SolveSessionId,
            cancellationToken);

        var latestMetadata = await _solveSessionsGateway.GetBySolveSessionIdAsync(
            metadata.SolveSessionId,
            cancellationToken);
        if (latestMetadata is null || SudokuSolveSessionStatus.IsTerminal(latestMetadata.Status))
        {
            return latestMetadata ?? metadata;
        }

        var finishedAtUtc = _timeProvider.GetUtcNow();
        var finalMetadata = string.Equals(latestMetadata.Status, SudokuSolveSessionStatus.Cancelling, StringComparison.OrdinalIgnoreCase)
                            || cancellationToken.IsCancellationRequested
                            || string.Equals(
                                solveResult.Outcome,
                                SudokuBacktrackingSolveResultDto.Cancelled,
                                StringComparison.Ordinal)
            ? SolveSessionStateTransitions.ToCancelled(latestMetadata, finishedAtUtc)
            : string.Equals(
                solveResult.Outcome,
                SudokuBacktrackingSolveResultDto.Completed,
                StringComparison.Ordinal)
                ? SolveSessionStateTransitions.ToCompleted(latestMetadata, finalGrid, finishedAtUtc)
                : SolveSessionStateTransitions.ToFailed(
                    latestMetadata,
                    finalGrid,
                    finishedAtUtc,
                    SolveSudokuErrorTypes.Unsolvable,
                    "Sudoku nie ma poprawnego rozwiązania.");

        await SaveAndPublishLockedAsync(finalMetadata, cancellationToken);
        return finalMetadata;
    }

    private async Task SaveAndPublishLockedAsync(
        SolveSessionMetadataDto metadata,
        CancellationToken cancellationToken)
    {
        await _solveSessionsGateway.UpdateAsync(metadata, cancellationToken);
        await _sudokuSolveEventPublisher.PublishAsync(ToSnapshot(metadata), cancellationToken);
    }

    private async Task ApplyInterStepDelayIfNeededAsync(
        SolveSessionMetadataDto? metadata,
        long acceptedSequence,
        CancellationToken cancellationToken)
    {
        if (metadata is null || acceptedSequence <= 0)
        {
            return;
        }

        var solverStepDelayMs = ResolveStoredSolverStepDelayMs(metadata);
        if (solverStepDelayMs <= 0)
        {
            return;
        }

        await Task.Delay(
            TimeSpan.FromMilliseconds(solverStepDelayMs),
            _timeProvider,
            cancellationToken);
    }

    private async Task TryFinalizeTechnicalFailureAsync(
        string solveSessionId,
        string status,
        string? errorType,
        string? message)
    {
        try
        {
            await using var solveSessionLock = await _solveSessionLockProvider.AcquireAsync(
                solveSessionId,
                CancellationToken.None);
            var latestMetadata = await _solveSessionsGateway.GetBySolveSessionIdAsync(solveSessionId, CancellationToken.None);
            if (latestMetadata is null || SudokuSolveSessionStatus.IsTerminal(latestMetadata.Status))
            {
                return;
            }

            var nowUtc = _timeProvider.GetUtcNow();
            var finalMetadata = string.Equals(status, SudokuSolveSessionStatus.Cancelled, StringComparison.OrdinalIgnoreCase)
                                || string.Equals(latestMetadata.Status, SudokuSolveSessionStatus.Cancelling, StringComparison.OrdinalIgnoreCase)
                ? SolveSessionStateTransitions.ToCancelled(latestMetadata, nowUtc)
                : SolveSessionStateTransitions.ToFailed(
                    latestMetadata,
                    latestMetadata.CurrentGrid,
                    nowUtc,
                    errorType,
                    message);

            await SaveAndPublishLockedAsync(finalMetadata, CancellationToken.None);
        }
        catch (Exception exception) when (exception is IOException
                                         or UnauthorizedAccessException
                                         or InvalidOperationException
                                         or FileStorageItemNotFoundException)
        {
            _ = exception;
        }
    }

    private static SolveSessionProgressSnapshotDto ToSnapshot(SolveSessionMetadataDto metadata)
    {
        return new SolveSessionProgressSnapshotDto(
            SolveSessionId: metadata.SolveSessionId,
            Status: metadata.Status,
            ProgressChannelUrl: metadata.ProgressChannelUrl,
            InputGrid: CopyGrid(metadata.InputGrid),
            CurrentGrid: CopyGrid(metadata.CurrentGrid),
            Sequence: metadata.LastAcceptedSequence,
            EventType: metadata.LastEventType,
            FailureErrorType: metadata.FailureErrorType,
            FailureMessage: metadata.FailureMessage,
            CreatedAtUtc: metadata.CreatedAtUtc,
            UpdatedAtUtc: metadata.UpdatedAtUtc,
            StartedAtUtc: metadata.StartedAtUtc,
            FinishedAtUtc: metadata.FinishedAtUtc);
    }

    private static int ResolveStoredSolverStepDelayMs(SolveSessionMetadataDto metadata)
    {
        return metadata.EffectiveParameters?.SolverStepDelayMs ?? 0;
    }

    private static int?[][] CopyGrid(int?[][] sourceGrid)
    {
        return sourceGrid
            .Select(row => row.ToArray())
            .ToArray();
    }
}
