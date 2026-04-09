namespace Sudoku.Contracts;

public sealed record ExampleFileApiResponse(
    string Name,
    string ContentType,
    long SizeBytes,
    DateTimeOffset StoredAtUtc);
