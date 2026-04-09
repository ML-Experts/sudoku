using MediatR;

namespace Sudoku.Application.Examples;

public sealed record PreprocessExampleCellsCommand(
    string? MimeType,
    string? Base64) : IRequest<PreprocessCellsResultDto>;
