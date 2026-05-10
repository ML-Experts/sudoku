using Sudoku.Application.ModelsActive;

namespace Sudoku.Application.Abstractions;

public interface IActiveModelPointerGateway
{
    Task<ActiveModelPointerDto?> GetAsync(
        CancellationToken cancellationToken = default);

    Task ReplaceAsync(
        ActiveModelPointerDto pointer,
        CancellationToken cancellationToken = default);
}
