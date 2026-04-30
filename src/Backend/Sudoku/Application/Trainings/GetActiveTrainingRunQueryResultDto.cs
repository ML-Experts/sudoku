namespace Sudoku.Application.Trainings;

public sealed record GetActiveTrainingRunQueryResultDto(
    bool HasActiveRun,
    ActiveTrainingRunDto? Run);
