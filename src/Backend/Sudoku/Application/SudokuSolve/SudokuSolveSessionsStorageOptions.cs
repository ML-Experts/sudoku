using System.ComponentModel.DataAnnotations;

namespace Sudoku.Application.SudokuSolve;

public sealed class SudokuSolveSessionsStorageOptions
{
    public const string SectionName = "SudokuSolveSessionsStorage";

    [Required]
    public string MetadataDirectoryPath { get; init; } = string.Empty;
}
