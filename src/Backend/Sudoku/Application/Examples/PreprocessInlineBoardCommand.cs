using MediatR;

namespace Sudoku.Application.Examples;

public sealed record PreprocessInlineBoardCommand(
    string? MimeType,
    string? Base64) : IRequest<PreprocessBoardResultDto>;
