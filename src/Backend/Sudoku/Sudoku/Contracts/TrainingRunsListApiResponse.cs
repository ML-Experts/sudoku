namespace Sudoku.Contracts;

public sealed record TrainingRunsListApiResponse(
    IReadOnlyList<TrainingRunListItemApiResponse> Items,
    int TotalCount);
