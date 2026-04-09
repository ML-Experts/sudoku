namespace Sudoku.Contracts;

public sealed record ImageApiResponse(
    string MimeType,
    string Base64);
