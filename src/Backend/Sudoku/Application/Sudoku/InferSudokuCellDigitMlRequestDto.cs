using Sudoku.Models.Images;

namespace Sudoku.Application.Sudoku;

public sealed record InferSudokuCellDigitMlRequestDto(
    ImageContent Image,
    InferSudokuCellDigitMlActiveModelDto ActiveModel,
    InferSudokuCellDigitMlResolvedConfigurationDto ResolvedConfiguration);

public sealed record InferSudokuCellDigitMlActiveModelDto(
    string Name,
    string ManifestPath,
    string PrimaryArtifactPath,
    string InputProfile);

public sealed record InferSudokuCellDigitMlResolvedConfigurationDto(
    string InferenceProfileName,
    double EmptyCellInnerMarginRatio,
    double EmptyCellDarkPixelRatioThreshold,
    double CenterAreaRatio,
    double MinComponentAreaRatio,
    double LineArtifactMinSpanRatio,
    double LineArtifactMaxThicknessRatio,
    int EmptyCellMinSegmentLengthPx,
    int EmptyCellFilteredSegmentCountThreshold
);
