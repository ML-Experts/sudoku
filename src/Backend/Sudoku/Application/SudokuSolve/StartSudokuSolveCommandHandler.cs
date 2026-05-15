using Sudoku.Application.Storage;
using Sudoku.Models.Sudoku;

namespace Sudoku.Application.SudokuSolve;

using MediatR;

public sealed class StartSudokuSolveCommandHandler
    : IRequestHandler<StartSudokuSolveCommand, StartSudokuSolveCommandResultDto>
{
    private const int MaxReservationAttempts = 10;

    private readonly ISolveSessionsGateway _solveSessionsGateway;
    private readonly ISudokuSolveExecutionScheduler _sudokuSolveExecutionScheduler;
    private readonly ISolveSessionIdGenerator _solveSessionIdGenerator;
    private readonly TimeProvider _timeProvider;

    public StartSudokuSolveCommandHandler(
        ISolveSessionsGateway solveSessionsGateway,
        ISudokuSolveExecutionScheduler sudokuSolveExecutionScheduler,
        ISolveSessionIdGenerator solveSessionIdGenerator,
        TimeProvider timeProvider)
    {
        _solveSessionsGateway = solveSessionsGateway;
        _sudokuSolveExecutionScheduler = sudokuSolveExecutionScheduler;
        _solveSessionIdGenerator = solveSessionIdGenerator;
        _timeProvider = timeProvider;
    }

    public async Task<StartSudokuSolveCommandResultDto> Handle(
        StartSudokuSolveCommand request,
        CancellationToken cancellationToken)
    {
        var inputGrid = ParseValidatedGrid(request);
        var domainGrid = new SudokuGrid(inputGrid);

        if (SudokuGridRules.TryFindConflict(domainGrid, out var conflictMessage))
        {
            throw new SudokuGridConflictsException(conflictMessage);
        }

        await EnsureNoActiveSessionAsync(cancellationToken);

        var createdAtUtc = _timeProvider.GetUtcNow();
        var metadata = await ReserveSolveSessionAsync(inputGrid, createdAtUtc, cancellationToken);

        try
        {
            await _sudokuSolveExecutionScheduler.ScheduleAsync(
                new SolveSessionWorkItemDto(metadata.SolveSessionId),
                cancellationToken);
        }
        catch (Exception exception) when (exception is InvalidOperationException or OperationCanceledException)
        {
            await RollbackReservationAfterScheduleFailureAsync(metadata, exception, cancellationToken);
            throw;
        }

        return new StartSudokuSolveCommandResultDto(
            SolveSessionId: metadata.SolveSessionId,
            Status: metadata.Status,
            ProgressChannelUrl: metadata.ProgressChannelUrl);
    }

    private static int?[][] ParseValidatedGrid(StartSudokuSolveCommand request)
    {
        if (!SudokuGridInputParser.TryParse(
                request.Grid,
                out var parsedGrid,
                out _,
                out _)
            || parsedGrid is null)
        {
            throw new InvalidOperationException("StartSudokuSolveCommand must be validated before handler execution.");
        }

        return parsedGrid;
    }

    private async Task EnsureNoActiveSessionAsync(CancellationToken cancellationToken)
    {
        IReadOnlyList<SolveSessionMetadataDto> sessions;
        try
        {
            sessions = await _solveSessionsGateway.ListAsync(cancellationToken);
        }
        catch (Exception exception) when (exception is IOException
                                         or UnauthorizedAccessException
                                         or InvalidDataException
                                         or InvalidOperationException)
        {
            throw new SolveSessionStartException(
                SolveSudokuErrorTypes.SolveSessionPersistenceFailed,
                "Nie udało się odczytać metadanych sesji rozwiązywania sudoku.",
                exception);
        }

        var activeSessions = sessions
            .Where(session => SudokuSolveSessionStatus.IsActive(session.Status))
            .OrderByDescending(session => session.CreatedAtUtc)
            .ToArray();

        if (activeSessions.Length > 1)
        {
            throw new SolveSessionStartException(
                SolveSudokuErrorTypes.SolveSessionInvariantViolation,
                "Wykryto więcej niż jedną aktywną sesję rozwiązywania sudoku.");
        }

        if (activeSessions.Length == 1)
        {
            throw new ActiveSolveSessionAlreadyExistsException(activeSessions[0].SolveSessionId);
        }
    }

    private async Task<SolveSessionMetadataDto> ReserveSolveSessionAsync(
        int?[][] inputGrid,
        DateTimeOffset createdAtUtc,
        CancellationToken cancellationToken)
    {
        for (var attempt = 0; attempt < MaxReservationAttempts; attempt++)
        {
            var solveSessionId = _solveSessionIdGenerator.Generate(createdAtUtc, attempt);
            var metadata = new SolveSessionMetadataDto(
                SolveSessionId: solveSessionId,
                Status: SudokuSolveSessionStatus.Queued,
                CreatedAtUtc: createdAtUtc,
                UpdatedAtUtc: createdAtUtc,
                ProgressChannelUrl: BuildProgressChannelUrl(solveSessionId),
                InputGrid: CopyGrid(inputGrid),
                CurrentGrid: CopyGrid(inputGrid));

            bool created;
            try
            {
                created = await _solveSessionsGateway.TryCreateAsync(metadata, cancellationToken);
            }
            catch (Exception exception) when (exception is IOException
                                             or UnauthorizedAccessException
                                             or InvalidOperationException)
            {
                throw new SolveSessionStartException(
                    SolveSudokuErrorTypes.SolveSessionPersistenceFailed,
                    "Nie udało się zapisać metadanych sesji rozwiązywania sudoku.",
                    exception);
            }

            if (created)
            {
                return metadata;
            }
        }

        throw new SolveSessionStartException(
            SolveSudokuErrorTypes.SolveSessionPersistenceFailed,
            "Nie udało się zarezerwować identyfikatora sesji rozwiązywania sudoku.");
    }

    private async Task RollbackReservationAfterScheduleFailureAsync(
        SolveSessionMetadataDto metadata,
        Exception cause,
        CancellationToken cancellationToken)
    {
        try
        {
            await _solveSessionsGateway.DeleteAsync(metadata.SolveSessionId, cancellationToken);
        }
        catch (Exception deleteException) when (deleteException is IOException
                                                or UnauthorizedAccessException
                                                or InvalidOperationException
                                                or FileStorageItemNotFoundException)
        {
            var failedMetadata = metadata with
            {
                Status = SudokuSolveSessionStatus.Failed,
                UpdatedAtUtc = _timeProvider.GetUtcNow(),
                FailureErrorType = SolveSudokuErrorTypes.SolveSessionEnqueueFailed,
                FailureMessage = "Nie udało się zlecić sesji rozwiązywania sudoku do wykonania w tle."
            };

            try
            {
                await _solveSessionsGateway.UpdateAsync(failedMetadata, cancellationToken);
            }
            catch (Exception updateException) when (updateException is IOException
                                                    or UnauthorizedAccessException
                                                    or InvalidOperationException
                                                    or FileStorageItemNotFoundException)
            {
                throw new SolveSessionStartException(
                    SolveSudokuErrorTypes.SolveSessionEnqueueFailed,
                    "Nie udało się zlecić sesji rozwiązywania sudoku do wykonania w tle.",
                    new AggregateException(cause, deleteException, updateException));
            }
        }

        throw new SolveSessionStartException(
            SolveSudokuErrorTypes.SolveSessionEnqueueFailed,
            "Nie udało się zlecić sesji rozwiązywania sudoku do wykonania w tle.",
            cause);
    }

    private static string BuildProgressChannelUrl(string solveSessionId)
    {
        return $"/ws/sudoku/solving/{solveSessionId}";
    }

    private static int?[][] CopyGrid(int?[][] sourceGrid)
    {
        return sourceGrid
            .Select(row => row.ToArray())
            .ToArray();
    }
}
