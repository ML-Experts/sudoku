namespace Sudoku.Application.Trainings;

public sealed record ListTrainingRunsQueryResultDto(
    IReadOnlyList<TrainingRunListItemDto> Items,
    int TotalCount);
