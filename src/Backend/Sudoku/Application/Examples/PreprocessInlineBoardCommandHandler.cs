using MediatR;
using Sudoku.Application.Abstractions;

namespace Sudoku.Application.Examples;

public sealed class PreprocessInlineBoardCommandHandler
    : IRequestHandler<PreprocessInlineBoardCommand, PreprocessBoardResultDto>
{
    private readonly IMlImageProcessingGateway _mlImageProcessingGateway;

    public PreprocessInlineBoardCommandHandler(IMlImageProcessingGateway mlImageProcessingGateway)
    {
        _mlImageProcessingGateway = mlImageProcessingGateway;
    }

    public async Task<PreprocessBoardResultDto> Handle(
        PreprocessInlineBoardCommand request,
        CancellationToken cancellationToken)
    {
        var sourceImage = InlineImagePayloadMapper.MapToImageContent(request.MimeType, request.Base64);
        var processedImage = await _mlImageProcessingGateway.PreprocessBoardAsync(sourceImage, cancellationToken);

        return new PreprocessBoardResultDto(
            MimeType: processedImage.MimeType,
            Base64: Convert.ToBase64String(processedImage.Content));
    }
}
