namespace Sudoku.Models.Images;

public sealed record ImageContent(
    string MimeType,
    byte[] Content);
