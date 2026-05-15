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
            metadata = await _solveSessionsGateway.GetBySolveSessionIdAsync(workItem.SolveSessionId, cancellationToken);
            if (metadata is null)
            {
                return;
            }

            if (SudokuSolveSessionStatus.IsTerminal(metadata.Status))
            {
                return;
            }

            metadata = await MarkRunningAsync(metadata, cancellationToken);

            var grid = new SudokuGrid(metadata.InputGrid);
            var sequence = metadata.LastAcceptedSequence ?? 0L;

            var solveResult = await _sudokuBacktrackingSolver.SolveAsync(
                grid,
                async (step, stepCancellationToken) =>
                {
                    sequence++;
                    metadata = await PersistProgressAsync(
                        metadata,
                        step,
                        sequence,
                        stepCancellationToken);
                },
                cancellationToken);

            metadata = await FinalizeSolveAsync(metadata, grid, solveResult, cancellationToken);
        }
        catch (OperationCanceledException) when (cancellationToken.IsCancellationRequested)
        {
            if (metadata is not null)
            {
                await TryFinalizeTechnicalFailureAsync(
                    metadata,
                    status: SudokuSolveSessionStatus.Cancelled,
                    eventType: SudokuSolveEventType.Cancelled,
                    errorType: null,
                    message: null);
            }
        }
        catch (Exception)
        {
            if (metadata is not null)
            {
                await TryFinalizeTechnicalFailureAsync(
                    metadata,
                    status: SudokuSolveSessionStatus.Failed,
                    eventType: SudokuSolveEventType.Failed,
                    errorType: SolveSudokuErrorTypes.SolveExecutionFailed,
                    message: "Nie udało się wykonać sesji rozwiązywania sudoku.");
            }
        }
    }

    private async Task<SolveSessionMetadataDto> MarkRunningAsync(
        SolveSessionMetadataDto metadata,
        CancellationToken cancellationToken)
    {
        var runningMetadata = metadata with
        {
            Status = SudokuSolveSessionStatus.Running,
            UpdatedAtUtc = _timeProvider.GetUtcNow(),
            StartedAtUtc = metadata.StartedAtUtc ?? _timeProvider.GetUtcNow(),
            LastEventType = SudokuSolveEventType.Snapshot,
            FailureErrorType = null,
            FailureMessage = null
        };

        await SaveAndPublishAsync(runningMetadata, cancellationToken);

        return runningMetadata;
    }

    private async Task<SolveSessionMetadataDto> PersistProgressAsync(
        SolveSessionMetadataDto metadata,
        SudokuSolverStepDto step,
        long sequence,
        CancellationToken cancellationToken)
    {
        var nextMetadata = metadata with
        {
            CurrentGrid = CopyGrid(step.CurrentGrid),
            UpdatedAtUtc = _timeProvider.GetUtcNow(),
            LastAcceptedSequence = sequence,
            LastEventType = step.EventType
        };

        await SaveAndPublishAsync(nextMetadata, cancellationToken);
        return nextMetadata;
    }

    private async Task<SolveSessionMetadataDto> FinalizeSolveAsync(
        SolveSessionMetadataDto metadata,
        SudokuGrid grid,
        SudokuBacktrackingSolveResultDto solveResult,
        CancellationToken cancellationToken)
    {
        var finishedAtUtc = _timeProvider.GetUtcNow();
        var finalGrid = grid.ToJaggedArray();
        var terminalSequence = GetNextTerminalSequence(metadata);

        var finalMetadata = solveResult.Outcome switch
        {
            SudokuBacktrackingSolveResultDto.Completed => metadata with
            {
                Status = SudokuSolveSessionStatus.Completed,
                CurrentGrid = finalGrid,
                UpdatedAtUtc = finishedAtUtc,
                FinishedAtUtc = finishedAtUtc,
                LastAcceptedSequence = terminalSequence,
                LastEventType = SudokuSolveEventType.Completed,
                FailureErrorType = null,
                FailureMessage = null
            },
            SudokuBacktrackingSolveResultDto.Cancelled => metadata with
            {
                Status = SudokuSolveSessionStatus.Cancelled,
                CurrentGrid = finalGrid,
                UpdatedAtUtc = finishedAtUtc,
                FinishedAtUtc = finishedAtUtc,
                LastAcceptedSequence = terminalSequence,
                LastEventType = SudokuSolveEventType.Cancelled
            },
            _ => metadata with
            {
                Status = SudokuSolveSessionStatus.Failed,
                CurrentGrid = finalGrid,
                UpdatedAtUtc = finishedAtUtc,
                FinishedAtUtc = finishedAtUtc,
                LastAcceptedSequence = terminalSequence,
                LastEventType = SudokuSolveEventType.Failed,
                FailureErrorType = SolveSudokuErrorTypes.Unsolvable,
                FailureMessage = "Sudoku nie ma poprawnego rozwiązania."
            }
        };

        await SaveAndPublishAsync(finalMetadata, cancellationToken);
        return finalMetadata;
    }

    private async Task SaveAndPublishAsync(
        SolveSessionMetadataDto metadata,
        CancellationToken cancellationToken)
    {
        await using var solveSessionLock = await _solveSessionLockProvider.AcquireAsync(
            metadata.SolveSessionId,
            cancellationToken);

        await _solveSessionsGateway.UpdateAsync(metadata, cancellationToken);
        await _sudokuSolveEventPublisher.PublishAsync(ToSnapshot(metadata), cancellationToken);
    }

    private async Task TryFinalizeTechnicalFailureAsync(
        SolveSessionMetadataDto metadata,
        string status,
        string eventType,
        string? errorType,
        string? message)
    {
        var finalMetadata = metadata with
        {
            Status = status,
            UpdatedAtUtc = _timeProvider.GetUtcNow(),
            FinishedAtUtc = _timeProvider.GetUtcNow(),
            LastAcceptedSequence = GetNextTerminalSequence(metadata),
            LastEventType = eventType,
            FailureErrorType = errorType,
            FailureMessage = message,
            CurrentGrid = metadata.CurrentGrid
        };

        try
        {
            await SaveAndPublishAsync(finalMetadata, CancellationToken.None);
        }
        catch (Exception exception) when (exception is IOException
                                         or UnauthorizedAccessException
                                         or InvalidOperationException
                                         or FileStorageItemNotFoundException)
        {
            _ = exception;
        }
    }

    private static long GetNextTerminalSequence(SolveSessionMetadataDto metadata)
    {
        return (metadata.LastAcceptedSequence ?? 0L) + 1L;
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

    private static int?[][] CopyGrid(int?[][] sourceGrid)
    {
        return sourceGrid
            .Select(row => row.ToArray())
            .ToArray();
    }
}
