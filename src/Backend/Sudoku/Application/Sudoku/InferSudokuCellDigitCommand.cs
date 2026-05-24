using MediatR;

namespace Sudoku.Application.Sudoku;

public sealed record InferSudokuCellDigitCommand(
    string? MimeType,
    string? Base64,
    double EmptyCellDarkPixelRatioThreshold,
    double EmptyCellInnerMarginRatio,
    double CenterAreaRatio,
    double MinComponentAreaRatio,
    double LineArtifactMinSpanRatio,
    double LineArtifactMaxThicknessRatio
) : IRequest<InferSudokuCellDigitCommandResultDto>;
