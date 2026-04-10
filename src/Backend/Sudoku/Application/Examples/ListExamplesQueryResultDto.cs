namespace Sudoku.Application.Examples;

public sealed record ListExamplesQueryResultDto(
    IReadOnlyList<ListExamplesItemDto> Items,
    int TotalCount);
