using Sudoku.Application.SudokuSolve;
using Sudoku.Contracts;
using Sudoku.Models.Sudoku;

namespace Sudoku.Realtime;

public static class SudokuSolveRealtimeResponseMapper
{
    public static SolveProgressEventApiResponse ToSnapshotApiResponse(
        SolveSessionRealtimeSnapshotDto snapshot)
    {
        return new SolveProgressEventApiResponse(
            EventType: SudokuSolveEventType.Snapshot,
            SolveSessionId: snapshot.SolveSessionId,
            Status: snapshot.Status,
            Sequence: snapshot.Sequence,
            CurrentGrid: CopyGrid(snapshot.CurrentGrid),
            ErrorType: snapshot.FailureErrorType,
            Message: snapshot.FailureMessage);
    }

    public static SolveProgressEventApiResponse ToProgressApiResponse(
        SolveSessionProgressSnapshotDto snapshot)
    {
        return new SolveProgressEventApiResponse(
            EventType: string.IsNullOrWhiteSpace(snapshot.EventType)
                ? SudokuSolveEventType.Progress
                : snapshot.EventType,
            SolveSessionId: snapshot.SolveSessionId,
            Status: snapshot.Status,
            Sequence: snapshot.Sequence ?? 0L,
            CurrentGrid: CopyGrid(snapshot.CurrentGrid),
            ErrorType: snapshot.FailureErrorType,
            Message: snapshot.FailureMessage);
    }

    private static int?[][] CopyGrid(int?[][] sourceGrid)
    {
        return sourceGrid
            .Select(row => row.ToArray())
            .ToArray();
    }
}
