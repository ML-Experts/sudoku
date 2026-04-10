namespace Sudoku.Application.Examples;

public sealed record ListExamplesItemDto(
    string Name,
    string ContentType,
    long SizeBytes,
    DateTimeOffset StoredAtUtc);
