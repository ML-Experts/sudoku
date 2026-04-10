namespace Sudoku.Application.Storage;

public sealed record StoredFileMetadataDto(
    string Name,
    long SizeBytes,
    DateTimeOffset LastModifiedUtc);
