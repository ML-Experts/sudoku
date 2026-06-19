namespace Sudoku.Contracts;

public sealed record DatasetPreparationsListApiResponse(
    IReadOnlyList<DatasetPreparationListItemApiResponse> Items,
    int TotalCount);
