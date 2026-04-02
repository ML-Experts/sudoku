namespace Sudoku.Contracts;

public sealed record ErrorApiResponse(
    string ErrorType,
    string Message);
