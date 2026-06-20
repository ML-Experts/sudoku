using Sudoku.Application.Abstractions;
using Sudoku.Application.Examples;
using Sudoku.Application.Ml;
using Sudoku.Application.Sudoku;
using Sudoku.Application.SudokuOverlay;
using Sudoku.Models.Images;

namespace Application.Tests;

public sealed class PreprocessInlineBoardCommandHandlerTests
{
    [Fact]
    public async Task Handle_MapsInlinePayloadAndReturnsProcessedImage()
    {
        var gateway = new StubMlImageProcessingGateway(
            preprocessBoardResult: new ImageContent("image/png", [9, 8, 7]));
        var handler = CreateHandler(gateway);

        var result = await handler.Handle(
            new PreprocessInlineBoardCommand(
                MimeType: "image/jpeg",
                Base64: Convert.ToBase64String([1, 2, 3])),
            CancellationToken.None);

        Assert.NotNull(gateway.LastPreprocessBoardImage);
        Assert.Equal("image/jpeg", gateway.LastPreprocessBoardImage!.MimeType);
        Assert.Equal([1, 2, 3], gateway.LastPreprocessBoardImage.Content);
        Assert.Equal("image/png", result.MimeType);
        Assert.Equal(Convert.ToBase64String([9, 8, 7]), result.Base64);
    }

    [Fact]
    public async Task Handle_PropagatesMlOperationFailedException()
    {
        var handler = CreateHandler(new StubMlImageProcessingGateway(
            preprocessBoardException: new MlOperationFailedException("board_not_found", "Brak planszy.")));

        var exception = await Assert.ThrowsAsync<MlOperationFailedException>(() => handler.Handle(
            new PreprocessInlineBoardCommand(
                MimeType: "image/png",
                Base64: Convert.ToBase64String([1, 2, 3])),
            CancellationToken.None));

        Assert.Equal("board_not_found", exception.ErrorType);
    }

    [Fact]
    public async Task Handle_PropagatesMlServiceTimeoutException()
    {
        var handler = CreateHandler(new StubMlImageProcessingGateway(
            preprocessBoardException: new MlServiceTimeoutException("timeout")));

        await Assert.ThrowsAsync<MlServiceTimeoutException>(() => handler.Handle(
            new PreprocessInlineBoardCommand(
                MimeType: "image/png",
                Base64: Convert.ToBase64String([1, 2, 3])),
            CancellationToken.None));
    }

    [Fact]
    public async Task Handle_PropagatesMlServiceUnavailableException()
    {
        var handler = CreateHandler(new StubMlImageProcessingGateway(
            preprocessBoardException: new MlServiceUnavailableException("unavailable")));

        await Assert.ThrowsAsync<MlServiceUnavailableException>(() => handler.Handle(
            new PreprocessInlineBoardCommand(
                MimeType: "image/png",
                Base64: Convert.ToBase64String([1, 2, 3])),
            CancellationToken.None));
    }

    private static PreprocessInlineBoardCommandHandler CreateHandler(IMlImageProcessingGateway gateway)
    {
        return new PreprocessInlineBoardCommandHandler(gateway);
    }

    private sealed class StubMlImageProcessingGateway : IMlImageProcessingGateway
    {
        private readonly ImageContent? _preprocessBoardResult;
        private readonly Exception? _preprocessBoardException;

        public StubMlImageProcessingGateway(
            ImageContent? preprocessBoardResult = null,
            Exception? preprocessBoardException = null)
        {
            _preprocessBoardResult = preprocessBoardResult;
            _preprocessBoardException = preprocessBoardException;
        }

        public ImageContent? LastPreprocessBoardImage { get; private set; }

        public Task<ImageContent> PreprocessBoardAsync(
            ImageContent image,
            CancellationToken cancellationToken = default)
        {
            LastPreprocessBoardImage = image;

            if (_preprocessBoardException is not null)
            {
                throw _preprocessBoardException;
            }

            return Task.FromResult(_preprocessBoardResult!);
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
            throw new NotSupportedException();
        }
    }
}
