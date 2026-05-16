using Sudoku.Models.Sudoku;

namespace Sudoku.Application.SudokuSolve;

public static class SolveSessionStateTransitions
{
    public static SolveSessionMetadataDto ToRunning(
        SolveSessionMetadataDto metadata,
        DateTimeOffset nowUtc)
    {
        return metadata with
        {
            Status = SudokuSolveSessionStatus.Running,
            UpdatedAtUtc = nowUtc,
            StartedAtUtc = metadata.StartedAtUtc ?? nowUtc,
            LastEventType = SudokuSolveEventType.Snapshot,
            FailureErrorType = null,
            FailureMessage = null
        };
    }

    public static SolveSessionMetadataDto ToCancelling(
        SolveSessionMetadataDto metadata,
        DateTimeOffset nowUtc)
    {
        return metadata with
        {
            Status = SudokuSolveSessionStatus.Cancelling,
            UpdatedAtUtc = nowUtc,
            FailureErrorType = null,
            FailureMessage = null
        };
    }

    public static SolveSessionMetadataDto ToCancelled(
        SolveSessionMetadataDto metadata,
        DateTimeOffset nowUtc)
    {
        return metadata with
        {
            Status = SudokuSolveSessionStatus.Cancelled,
            UpdatedAtUtc = nowUtc,
            FinishedAtUtc = nowUtc,
            LastAcceptedSequence = GetNextTerminalSequence(metadata),
            LastEventType = SudokuSolveEventType.Cancelled,
            FailureErrorType = null,
            FailureMessage = null,
            CurrentGrid = CopyGrid(metadata.CurrentGrid)
        };
    }

    public static SolveSessionMetadataDto ToCompleted(
        SolveSessionMetadataDto metadata,
        int?[][] finalGrid,
        DateTimeOffset nowUtc)
    {
        return metadata with
        {
            Status = SudokuSolveSessionStatus.Completed,
            CurrentGrid = CopyGrid(finalGrid),
            UpdatedAtUtc = nowUtc,
            FinishedAtUtc = nowUtc,
            LastAcceptedSequence = GetNextTerminalSequence(metadata),
            LastEventType = SudokuSolveEventType.Completed,
            FailureErrorType = null,
            FailureMessage = null
        };
    }

    public static SolveSessionMetadataDto ToFailed(
        SolveSessionMetadataDto metadata,
        int?[][] currentGrid,
        DateTimeOffset nowUtc,
        string? failureErrorType,
        string? failureMessage)
    {
        return metadata with
        {
            Status = SudokuSolveSessionStatus.Failed,
            CurrentGrid = CopyGrid(currentGrid),
            UpdatedAtUtc = nowUtc,
            FinishedAtUtc = nowUtc,
            LastAcceptedSequence = GetNextTerminalSequence(metadata),
            LastEventType = SudokuSolveEventType.Failed,
            FailureErrorType = failureErrorType,
            FailureMessage = failureMessage
        };
    }

    private static long GetNextTerminalSequence(SolveSessionMetadataDto metadata)
    {
        return (metadata.LastAcceptedSequence ?? 0L) + 1L;
    }

    private static int?[][] CopyGrid(int?[][] sourceGrid)
    {
        return sourceGrid
            .Select(row => row.ToArray())
            .ToArray();
    }
}
