using Sudoku.Models.Images;
using Sudoku.Application.Sudoku;

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
}
