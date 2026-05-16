namespace Sudoku.Application.Abstractions;

public interface IBackgroundOperationCancellationRegistry
{
    CancellationToken Register(string operationId);

    bool TryGetCancellationToken(string operationId, out CancellationToken cancellationToken);

    bool TryCancel(string operationId);

    void Complete(string operationId);
}
