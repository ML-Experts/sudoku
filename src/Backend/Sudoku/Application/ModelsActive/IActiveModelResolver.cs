namespace Sudoku.Application.ModelsActive;

public interface IActiveModelResolver
{
    Task<ResolvedActiveModelDto?> ResolveForInferenceAsync(
        CancellationToken cancellationToken = default);
}
