namespace Sudoku.Contracts;

public sealed record ExamplesListApiResponse(
    IReadOnlyList<ExampleFileApiResponse> Items,
    int TotalCount);
