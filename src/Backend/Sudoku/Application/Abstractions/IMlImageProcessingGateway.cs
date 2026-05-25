using Sudoku.Models.Images;
using Sudoku.Application.Sudoku;
using Sudoku.Application.SudokuOverlay;

namespace Sudoku.Application.Abstractions;

public interface IMlImageProcessingGateway
{
    Task<ImageContent> PreprocessBoardAsync(
        ImageContent image,
        CancellationToken cancellationToken = default);

    Task<CellsGrid> ExtractCellsAsync(
        ImageContent image,
        CancellationToken cancellationToken = default);

    Task<InferSudokuCellDigitMlResultDto> InferDigitAsync(
        InferSudokuCellDigitMlRequestDto request,
        CancellationToken cancellationToken = default);

    Task<ImageContent> RenderOverlayCellAsync(
        RenderSudokuOverlayCellMlRequestDto request,
        CancellationToken cancellationToken = default);
}
