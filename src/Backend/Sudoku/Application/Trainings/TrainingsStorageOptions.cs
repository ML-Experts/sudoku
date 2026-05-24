using System.ComponentModel.DataAnnotations;

namespace Sudoku.Application.Trainings;

public sealed class TrainingsStorageOptions
{
    public const string SectionName = "TrainingsStorage";

    [Required]
    public string RunsDirectoryPath { get; init; } = string.Empty;

    [Required]
    public string ReportsDirectoryPath { get; init; } = string.Empty;

    [Required]
    public string MetadataDirectoryPath { get; init; } = string.Empty;

    [Required]
    public string WorkingDirectoryPath { get; init; } = string.Empty;
}
