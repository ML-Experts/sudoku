using Sudoku.Models.Images;

namespace Sudoku.Application.Abstractions;

public interface IMlImageProcessingGateway
{
    Task<ImageContent> PreprocessBoardAsync(
        ImageContent image,
        CancellationToken cancellationToken = default);

    Task<CellsGrid> ExtractCellsAsync(
        ImageContent image,
        CancellationToken cancellationToken = default);
}
