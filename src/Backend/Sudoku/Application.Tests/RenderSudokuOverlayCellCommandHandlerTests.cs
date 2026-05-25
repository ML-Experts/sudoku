using Sudoku.Application.Abstractions;
using Sudoku.Application.Ml;
using Sudoku.Application.Sudoku;
using Sudoku.Application.SudokuOverlay;
using Sudoku.Models.Images;
using Sudoku.Models.Sudoku;

namespace Application.Tests;

public sealed class RenderSudokuOverlayCellCommandHandlerTests
{
    [Fact]
    public async Task Handle_PassesDigitAndPositionToMlRequest()
    {
        var mlGateway = new StubMlImageProcessingGateway(new ImageContent("image/png", [9, 8, 7]));
        var handler = new RenderSudokuOverlayCellCommandHandler(mlGateway);

        var command = new RenderSudokuOverlayCellCommand(
            CellImageMimeType: "image/png",
            CellImageBase64: Convert.ToBase64String([1, 2, 3]),
            Digit: 4,
            RowIndex: 0,
            ColumnIndex: 2);

        var result = await handler.Handle(command, CancellationToken.None);

        Assert.Equal("image/png", result.MimeType);
        Assert.Equal(Convert.ToBase64String([9, 8, 7]), result.Base64);
        Assert.NotNull(mlGateway.LastOverlayRequest);
        Assert.Equal(4, mlGateway.LastOverlayRequest!.Digit);
        Assert.Equal(new SudokuCellPosition(0, 2), mlGateway.LastOverlayRequest.CellPosition);
        Assert.Equal([1, 2, 3], mlGateway.LastOverlayRequest.CellImage.Content);
    }

    [Fact]
    public async Task Handle_AllowsRequestWithoutPosition()
    {
        var mlGateway = new StubMlImageProcessingGateway(new ImageContent("image/png", [9, 8, 7]));
        var handler = new RenderSudokuOverlayCellCommandHandler(mlGateway);

        var command = new RenderSudokuOverlayCellCommand(
            CellImageMimeType: "image/png",
            CellImageBase64: Convert.ToBase64String([1, 2, 3]),
            Digit: 7,
            RowIndex: null,
            ColumnIndex: null);

        await handler.Handle(command, CancellationToken.None);

        Assert.NotNull(mlGateway.LastOverlayRequest);
        Assert.Null(mlGateway.LastOverlayRequest!.CellPosition);
    }

    [Fact]
    public async Task Handle_ThrowsMlInvalidResponse_WhenReturnedMimeTypeIsEmpty()
    {
        var mlGateway = new StubMlImageProcessingGateway(new ImageContent(string.Empty, [9, 8, 7]));
        var handler = new RenderSudokuOverlayCellCommandHandler(mlGateway);

        var exception = await Assert.ThrowsAsync<MlOperationFailedException>(() => handler.Handle(
            CreateCommand(),
            CancellationToken.None));

        Assert.Equal(RenderSudokuOverlayCellErrorTypes.MlInvalidResponse, exception.ErrorType);
    }

    [Fact]
    public async Task Handle_ThrowsMlInvalidResponse_WhenReturnedImageIsEmpty()
    {
        var mlGateway = new StubMlImageProcessingGateway(new ImageContent("image/png", []));
        var handler = new RenderSudokuOverlayCellCommandHandler(mlGateway);

        var exception = await Assert.ThrowsAsync<MlOperationFailedException>(() => handler.Handle(
            CreateCommand(),
            CancellationToken.None));

        Assert.Equal(RenderSudokuOverlayCellErrorTypes.MlInvalidResponse, exception.ErrorType);
    }

    private static RenderSudokuOverlayCellCommand CreateCommand()
    {
        return new RenderSudokuOverlayCellCommand(
            CellImageMimeType: "image/png",
            CellImageBase64: Convert.ToBase64String([1, 2, 3]),
            Digit: 4,
            RowIndex: null,
            ColumnIndex: null);
    }

    private sealed class StubMlImageProcessingGateway : IMlImageProcessingGateway
    {
        private readonly ImageContent _overlayResponse;

        public StubMlImageProcessingGateway(ImageContent overlayResponse)
        {
            _overlayResponse = overlayResponse;
        }

        public RenderSudokuOverlayCellMlRequestDto? LastOverlayRequest { get; private set; }

        public Task<ImageContent> PreprocessBoardAsync(
            ImageContent image,
            CancellationToken cancellationToken = default)
        {
            throw new NotSupportedException();
        }

        public Task<CellsGrid> ExtractCellsAsync(
            ImageContent image,
            CancellationToken cancellationToken = default)
        {
            throw new NotSupportedException();
        }

        public Task<InferSudokuCellDigitMlResultDto> InferDigitAsync(
            InferSudokuCellDigitMlRequestDto request,
            CancellationToken cancellationToken = default)
        {
            throw new NotSupportedException();
        }

        public Task<ImageContent> RenderOverlayCellAsync(
            RenderSudokuOverlayCellMlRequestDto request,
            CancellationToken cancellationToken = default)
        {
            LastOverlayRequest = request;
            return Task.FromResult(_overlayResponse);
        }
    }
}
