namespace Sudoku.Contracts;

public sealed record RegistryModelsListApiResponse(
    IReadOnlyList<RegistryModelListItemApiResponse> Items,
    int TotalCount);
