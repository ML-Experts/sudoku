using MediatR;
using Sudoku.Application.Abstractions;
using Sudoku.Application.Ml;
using Sudoku.Models.Images;
using Sudoku.Models.Sudoku;

namespace Sudoku.Application.SudokuOverlay;

public sealed class RenderSudokuOverlayCellCommandHandler
    : IRequestHandler<RenderSudokuOverlayCellCommand, RenderSudokuOverlayCellCommandResultDto>
{
    private readonly IMlImageProcessingGateway _mlImageProcessingGateway;

    public RenderSudokuOverlayCellCommandHandler(IMlImageProcessingGateway mlImageProcessingGateway)
    {
        _mlImageProcessingGateway = mlImageProcessingGateway;
    }

    public async Task<RenderSudokuOverlayCellCommandResultDto> Handle(
        RenderSudokuOverlayCellCommand request,
        CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(request.CellImageMimeType) || string.IsNullOrWhiteSpace(request.CellImageBase64))
        {
            throw new InvalidOperationException("RenderSudokuOverlayCellCommand must be validated before handler execution.");
        }

        byte[] imageBytes;
        try
        {
            imageBytes = Convert.FromBase64String(request.CellImageBase64);
        }
        catch (FormatException)
        {
            throw new InvalidOperationException("RenderSudokuOverlayCellCommand contains invalid Base64 payload.");
        }

        var requestImage = new ImageContent(
            MimeType: request.CellImageMimeType,
            Content: imageBytes);

        SudokuCellPosition? cellPosition = null;
        if (request.RowIndex.HasValue && request.ColumnIndex.HasValue)
        {
            cellPosition = new SudokuCellPosition(request.RowIndex.Value, request.ColumnIndex.Value);
        }

        var mlRequest = new RenderSudokuOverlayCellMlRequestDto(
            CellImage: requestImage,
            Digit: request.Digit,
            CellPosition: cellPosition);

        var renderedImage = await _mlImageProcessingGateway.RenderOverlayCellAsync(mlRequest, cancellationToken);

        if (string.IsNullOrWhiteSpace(renderedImage.MimeType))
        {
            throw new MlOperationFailedException(
                RenderSudokuOverlayCellErrorTypes.MlInvalidResponse,
                "Serwis ML zwrócił obraz bez pola mimeType.");
        }

        if (renderedImage.Content.Length == 0)
        {
            throw new MlOperationFailedException(
                RenderSudokuOverlayCellErrorTypes.MlInvalidResponse,
                "Serwis ML zwrócił pusty obraz overlay.");
        }

        return new RenderSudokuOverlayCellCommandResultDto(
            MimeType: renderedImage.MimeType,
            Base64: Convert.ToBase64String(renderedImage.Content));
    }
}
