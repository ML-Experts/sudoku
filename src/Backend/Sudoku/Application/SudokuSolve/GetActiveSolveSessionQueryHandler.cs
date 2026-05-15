using MediatR;
using Sudoku.Models.Sudoku;

namespace Sudoku.Application.SudokuSolve;

public sealed class GetActiveSolveSessionQueryHandler
    : IRequestHandler<GetActiveSolveSessionQuery, GetActiveSolveSessionQueryResultDto>
{
    private readonly ISolveSessionsGateway _solveSessionsGateway;

    public GetActiveSolveSessionQueryHandler(ISolveSessionsGateway solveSessionsGateway)
    {
        _solveSessionsGateway = solveSessionsGateway;
    }

    public async Task<GetActiveSolveSessionQueryResultDto> Handle(
        GetActiveSolveSessionQuery request,
        CancellationToken cancellationToken)
    {
        var sessions = await _solveSessionsGateway.ListAsync(cancellationToken);
        var activeSessions = sessions
            .Where(session => SudokuSolveSessionStatus.IsActive(session.Status))
            .OrderByDescending(session => session.CreatedAtUtc)
            .ToArray();

        if (activeSessions.Length == 0)
        {
            return new GetActiveSolveSessionQueryResultDto(
                HasActiveSession: false,
                Session: null);
        }

        if (activeSessions.Length > 1)
        {
            throw new InvalidOperationException(
                "Detected more than one active sudoku solve session. This violates the single active session invariant.");
        }

        var activeSession = activeSessions[0];
        if (string.IsNullOrWhiteSpace(activeSession.ProgressChannelUrl))
        {
            throw new InvalidOperationException(
                "Active sudoku solve session does not contain a valid progressChannelUrl.");
        }

        return new GetActiveSolveSessionQueryResultDto(
            HasActiveSession: true,
            Session: new ActiveSolveSessionDto(
                SolveSessionId: activeSession.SolveSessionId,
                Status: activeSession.Status,
                ProgressChannelUrl: activeSession.ProgressChannelUrl));
    }
}
