namespace Sudoku.Contracts;

public sealed record ProcessedDatasetsListApiResponse(
    IReadOnlyList<ProcessedDatasetListItemApiResponse> Items,
    int TotalCount);
