using System.ComponentModel.DataAnnotations;

namespace Sudoku.Application.SudokuOverlay;

public sealed class SudokuOverlayOptions
{
    public const string SectionName = "SudokuOverlay";

    [Range(1, int.MaxValue)]
    public int MaxInlineCellImageSizeBytes { get; init; } = 10 * 1024 * 1024;
}
