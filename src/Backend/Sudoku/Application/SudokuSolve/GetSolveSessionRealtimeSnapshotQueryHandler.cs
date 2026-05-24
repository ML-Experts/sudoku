using MediatR;
using Sudoku.Models.Sudoku;

namespace Sudoku.Application.SudokuSolve;

public sealed class GetSolveSessionRealtimeSnapshotQueryHandler
    : IRequestHandler<GetSolveSessionRealtimeSnapshotQuery, GetSolveSessionRealtimeSnapshotResultDto>
{
    private readonly ISolveSessionsGateway _solveSessionsGateway;

    public GetSolveSessionRealtimeSnapshotQueryHandler(ISolveSessionsGateway solveSessionsGateway)
    {
        _solveSessionsGateway = solveSessionsGateway;
    }

    public async Task<GetSolveSessionRealtimeSnapshotResultDto> Handle(
        GetSolveSessionRealtimeSnapshotQuery request,
        CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(request.SolveSessionId))
        {
            throw new InvalidOperationException(
                "GetSolveSessionRealtimeSnapshotQuery must be validated before handler execution.");
        }

        var solveSessionId = request.SolveSessionId.Trim();
        var metadata = await _solveSessionsGateway.GetBySolveSessionIdAsync(solveSessionId, cancellationToken);
        if (metadata is null)
        {
            throw new SolveSessionNotFoundForRealtimeException(solveSessionId);
        }

        return new GetSolveSessionRealtimeSnapshotResultDto(ToSnapshot(metadata));
    }

    private static SolveSessionRealtimeSnapshotDto ToSnapshot(SolveSessionMetadataDto metadata)
    {
        return new SolveSessionRealtimeSnapshotDto(
            SolveSessionId: metadata.SolveSessionId,
            Status: metadata.Status,
            Sequence: metadata.LastAcceptedSequence ?? 0L,
            EventType: string.IsNullOrWhiteSpace(metadata.LastEventType)
                ? SudokuSolveEventType.Snapshot
                : metadata.LastEventType,
            CurrentGrid: CopyGrid(metadata.CurrentGrid),
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
