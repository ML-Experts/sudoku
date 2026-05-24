using System.ComponentModel.DataAnnotations;

namespace Sudoku.Application.Trainings;

public sealed class TrainingRecoveryOptions
{
    public const string SectionName = "TrainingRecovery";

    [Range(1, int.MaxValue)]
    public int StaleCancellingTimeoutSeconds { get; init; } = 300;
}
