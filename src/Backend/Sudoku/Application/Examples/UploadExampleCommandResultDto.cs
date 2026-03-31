namespace Sudoku.Application.Examples;

public sealed record UploadExampleCommandResultDto(
    string Name,
    string ContentType,
    long SizeBytes,
    DateTimeOffset StoredAtUtc);
