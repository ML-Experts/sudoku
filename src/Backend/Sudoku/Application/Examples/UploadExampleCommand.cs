using MediatR;

namespace Sudoku.Application.Examples;

public sealed record UploadExampleCommand(
    Stream? FileStream,
    string? ContentType,
    long? SizeBytes) : IRequest<UploadExampleCommandResultDto>;
