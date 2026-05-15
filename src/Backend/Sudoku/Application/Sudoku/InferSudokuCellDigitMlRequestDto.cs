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
    double EmptyCellDarkPixelRatioThreshold);
