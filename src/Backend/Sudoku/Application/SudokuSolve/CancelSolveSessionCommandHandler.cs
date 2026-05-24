using MediatR;
using Sudoku.Application.Abstractions;
using Sudoku.Application.Storage;
using Sudoku.Models.Sudoku;

namespace Sudoku.Application.SudokuSolve;

public sealed class CancelSolveSessionCommandHandler
    : IRequestHandler<CancelSolveSessionCommand, CancelSolveSessionCommandResultDto>
{
    private readonly ISolveSessionsGateway _solveSessionsGateway;
    private readonly IBackgroundOperationCancellationRegistry _backgroundOperationCancellationRegistry;
    private readonly ISudokuSolveEventPublisher _sudokuSolveEventPublisher;
    private readonly ISolveSessionLockProvider _solveSessionLockProvider;
    private readonly TimeProvider _timeProvider;

    public CancelSolveSessionCommandHandler(
        ISolveSessionsGateway solveSessionsGateway,
        IBackgroundOperationCancellationRegistry backgroundOperationCancellationRegistry,
        ISudokuSolveEventPublisher sudokuSolveEventPublisher,
        ISolveSessionLockProvider solveSessionLockProvider,
        TimeProvider timeProvider)
    {
        _solveSessionsGateway = solveSessionsGateway;
        _backgroundOperationCancellationRegistry = backgroundOperationCancellationRegistry;
        _sudokuSolveEventPublisher = sudokuSolveEventPublisher;
        _solveSessionLockProvider = solveSessionLockProvider;
        _timeProvider = timeProvider;
    }

    public async Task<CancelSolveSessionCommandResultDto> Handle(
        CancelSolveSessionCommand request,
        CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(request.SolveSessionId))
        {
            throw new InvalidOperationException("CancelSolveSessionCommand must be validated before handler execution.");
        }

        var solveSessionId = request.SolveSessionId.Trim();
        await using var solveSessionLock = await _solveSessionLockProvider.AcquireAsync(solveSessionId, cancellationToken);

        var metadata = await ReadMetadataAsync(solveSessionId, cancellationToken);
        if (metadata is null)
        {
            return new CancelSolveSessionCommandResultDto(
                Status: null,
                RequestDisposition: CancelSolveSessionDispositions.NotFound);
        }

        await EnsureSingleActiveSessionInvariantAsync(metadata, cancellationToken);

        if (SudokuSolveSessionStatus.IsTerminal(metadata.Status))
        {
            return new CancelSolveSessionCommandResultDto(
                Status: metadata.Status,
                RequestDisposition: CancelSolveSessionDispositions.AlreadyFinished);
        }

        if (string.Equals(metadata.Status, SudokuSolveSessionStatus.Cancelling, StringComparison.OrdinalIgnoreCase))
        {
            if (_backgroundOperationCancellationRegistry.TryCancel(solveSessionId))
            {
                return new CancelSolveSessionCommandResultDto(
                    Status: SudokuSolveSessionStatus.Cancelling,
                    RequestDisposition: CancelSolveSessionDispositions.Duplicate);
            }

            var cancelledMetadata = await FinalizeCancelledWithoutLiveExecutionAsync(metadata, cancellationToken);
            return new CancelSolveSessionCommandResultDto(
                Status: cancelledMetadata.Status,
                RequestDisposition: CancelSolveSessionDispositions.Accepted);
        }

        if (!SudokuSolveSessionStatus.CanRequestCancellation(metadata.Status))
        {
            throw new InvalidOperationException(
                $"Unexpected sudoku solve session status '{metadata.Status}' during cancellation.");
        }

        var cancellingMetadata = SolveSessionStateTransitions.ToCancelling(metadata, _timeProvider.GetUtcNow());
        await UpdateMetadataAsync(cancellingMetadata, cancellationToken);

        if (_backgroundOperationCancellationRegistry.TryCancel(solveSessionId))
        {
            return new CancelSolveSessionCommandResultDto(
                Status: SudokuSolveSessionStatus.Cancelling,
                RequestDisposition: CancelSolveSessionDispositions.Accepted);
        }

        var finalCancelledMetadata = await FinalizeCancelledWithoutLiveExecutionAsync(cancellingMetadata, cancellationToken);
        return new CancelSolveSessionCommandResultDto(
            Status: finalCancelledMetadata.Status,
            RequestDisposition: CancelSolveSessionDispositions.Accepted);
    }

    private async Task EnsureSingleActiveSessionInvariantAsync(
        SolveSessionMetadataDto requestedMetadata,
        CancellationToken cancellationToken)
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
            throw new SolveSessionCancelPersistenceException(
                "Nie udało się odczytać metadanych sesji rozwiązywania sudoku podczas anulowania.",
                exception);
        }

        var activeSessions = sessions
            .Where(session => SudokuSolveSessionStatus.IsActive(session.Status))
            .ToArray();

        if (activeSessions.Length > 1)
        {
            throw new InvalidOperationException(
                "Detected more than one active sudoku solve session. This violates the single active session invariant.");
        }

        if (activeSessions.Length == 1
            && SudokuSolveSessionStatus.IsActive(requestedMetadata.Status)
            && !string.Equals(activeSessions[0].SolveSessionId, requestedMetadata.SolveSessionId, StringComparison.Ordinal))
        {
            throw new InvalidOperationException(
                "Detected active sudoku solve session mismatch. This violates the single active session invariant.");
        }
    }

    private async Task<SolveSessionMetadataDto?> ReadMetadataAsync(
        string solveSessionId,
        CancellationToken cancellationToken)
    {
        try
        {
            return await _solveSessionsGateway.GetBySolveSessionIdAsync(solveSessionId, cancellationToken);
        }
        catch (Exception exception) when (exception is IOException
                                         or UnauthorizedAccessException
                                         or InvalidDataException
                                         or InvalidOperationException)
        {
            throw new SolveSessionCancelPersistenceException(
                "Nie udało się odczytać metadanych sesji rozwiązywania sudoku podczas anulowania.",
                exception);
        }
    }

    private async Task UpdateMetadataAsync(
        SolveSessionMetadataDto metadata,
        CancellationToken cancellationToken)
    {
        try
        {
            await _solveSessionsGateway.UpdateAsync(metadata, cancellationToken);
        }
        catch (Exception exception) when (exception is IOException
                                         or UnauthorizedAccessException
                                         or InvalidOperationException
                                         or FileStorageItemNotFoundException)
        {
            throw new SolveSessionCancelPersistenceException(
                "Nie udało się zapisać metadanych anulowania sesji rozwiązywania sudoku.",
                exception);
        }
    }

    private async Task<SolveSessionMetadataDto> FinalizeCancelledWithoutLiveExecutionAsync(
        SolveSessionMetadataDto metadata,
        CancellationToken cancellationToken)
    {
        var cancelledMetadata = SolveSessionStateTransitions.ToCancelled(metadata, _timeProvider.GetUtcNow());
        await UpdateMetadataAsync(cancelledMetadata, cancellationToken);
        await _sudokuSolveEventPublisher.PublishAsync(ToSnapshot(cancelledMetadata), cancellationToken);
        return cancelledMetadata;
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
