namespace Sudoku.Application.Storage;

public sealed record StoredDirectoryMetadataDto(
    string Name,
    DateTimeOffset LastModifiedUtc);
