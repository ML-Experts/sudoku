namespace Sudoku.Application.SudokuSolve;

public interface ISolveSessionsGateway
{
    Task<IReadOnlyList<SolveSessionMetadataDto>> ListAsync(
        CancellationToken cancellationToken = default);

    Task<SolveSessionMetadataDto?> GetBySolveSessionIdAsync(
        string solveSessionId,
        CancellationToken cancellationToken = default);

    Task<bool> TryCreateAsync(
        SolveSessionMetadataDto metadata,
        CancellationToken cancellationToken = default);

    Task UpdateAsync(
        SolveSessionMetadataDto metadata,
        CancellationToken cancellationToken = default);

    Task DeleteAsync(
        string solveSessionId,
        CancellationToken cancellationToken = default);
}
