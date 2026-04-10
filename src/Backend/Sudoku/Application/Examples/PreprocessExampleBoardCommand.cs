using MediatR;

namespace Sudoku.Application.Examples;

public sealed record PreprocessExampleBoardCommand(string? Name) : IRequest<PreprocessBoardResultDto>;
