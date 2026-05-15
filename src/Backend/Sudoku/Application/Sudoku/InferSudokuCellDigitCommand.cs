using MediatR;

namespace Sudoku.Application.Sudoku;

public sealed record InferSudokuCellDigitCommand(
    string? MimeType,
    string? Base64) : IRequest<InferSudokuCellDigitCommandResultDto>;
