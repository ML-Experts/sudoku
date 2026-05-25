using FluentValidation;
using FluentValidation.Results;
using MediatR;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging.Abstractions;
using Sudoku.Application.Ml;
using Sudoku.Application.SudokuOverlay;
using Sudoku.Controllers;
using Sudoku.Contracts;

namespace Application.Tests;

public sealed class SudokuOverlayControllerTests
{
    [Fact]
    public async Task RenderCellAsync_PassesDigitAndPositionToCommand()
    {
        var sender = new StubSender(new RenderSudokuOverlayCellCommandResultDto(
            MimeType: "image/png",
            Base64: Convert.ToBase64String([9, 8, 7])));
        var controller = CreateController(sender);

        var result = await controller.RenderCellAsync(
            new RenderSudokuOverlayCellApiEntry(
                CellImage: new ImageApiEntry("image/png", Convert.ToBase64String([1, 2, 3])),
                Digit: 4,
                RowIndex: 0,
                ColumnIndex: 2),
            CancellationToken.None);

        var okResult = Assert.IsType<OkObjectResult>(result);
        Assert.Equal(StatusCodes.Status200OK, okResult.StatusCode);

        var command = Assert.IsType<RenderSudokuOverlayCellCommand>(sender.LastRequest);
        Assert.Equal(4, command.Digit);
        Assert.Equal(0, command.RowIndex);
        Assert.Equal(2, command.ColumnIndex);
        Assert.Equal("image/png", command.CellImageMimeType);
    }

    [Fact]
    public async Task RenderCellAsync_ReturnsUnprocessableEntity_WhenMlRejectsCell()
    {
        var sender = new StubSender(new MlOperationFailedException(
            RenderSudokuOverlayCellErrorTypes.CellImageNotProcessable,
            "Komórka nie może zostać przetworzona."));
        var controller = CreateController(sender);

        var result = await controller.RenderCellAsync(
            new RenderSudokuOverlayCellApiEntry(
                CellImage: new ImageApiEntry("image/png", Convert.ToBase64String([1, 2, 3])),
                Digit: 4,
                RowIndex: null,
                ColumnIndex: null),
            CancellationToken.None);

        var unprocessableResult = Assert.IsType<UnprocessableEntityObjectResult>(result);
        Assert.Equal(StatusCodes.Status422UnprocessableEntity, unprocessableResult.StatusCode);
    }

    [Fact]
    public async Task RenderCellAsync_ReturnsBadRequest_WhenValidationFails()
    {
        var sender = new StubSender(new ValidationException([
            new ValidationFailure("Digit", "Pole 'digit' musi zawierać wartość z zakresu 1..9.")
            {
                ErrorCode = RenderSudokuOverlayCellErrorTypes.DigitOutOfRange
            }
        ]));
        var controller = CreateController(sender);

        var result = await controller.RenderCellAsync(
            new RenderSudokuOverlayCellApiEntry(
                CellImage: new ImageApiEntry("image/png", Convert.ToBase64String([1, 2, 3])),
                Digit: 0,
                RowIndex: null,
                ColumnIndex: null),
            CancellationToken.None);

        var badRequestResult = Assert.IsType<BadRequestObjectResult>(result);
        Assert.Equal(StatusCodes.Status400BadRequest, badRequestResult.StatusCode);

        var payload = Assert.IsType<ErrorApiResponse>(badRequestResult.Value);
        Assert.Equal(RenderSudokuOverlayCellErrorTypes.DigitOutOfRange, payload.ErrorType);
    }

    private static SudokuOverlayController CreateController(ISender sender)
    {
        return new SudokuOverlayController(
            sender,
            NullLogger<SudokuOverlayController>.Instance);
    }

    private sealed class StubSender : ISender
    {
        private readonly object? _response;
        private readonly Exception? _exception;

        public object? LastRequest { get; private set; }

        public StubSender(object response)
        {
            _response = response;
        }

        public StubSender(Exception exception)
        {
            _exception = exception;
        }

        public Task<TResponse> Send<TResponse>(
            IRequest<TResponse> request,
            CancellationToken cancellationToken = default)
        {
            LastRequest = request;

            if (_exception is not null)
            {
                throw _exception;
            }

            return Task.FromResult((TResponse)_response!);
        }

        public Task Send<TRequest>(TRequest request, CancellationToken cancellationToken = default)
            where TRequest : IRequest
        {
            LastRequest = request;

            if (_exception is not null)
            {
                throw _exception;
            }

            return Task.CompletedTask;
        }

        public IAsyncEnumerable<TResponse> CreateStream<TResponse>(
            IStreamRequest<TResponse> request,
            CancellationToken cancellationToken = default)
        {
            throw new NotSupportedException();
        }

        public IAsyncEnumerable<object?> CreateStream(
            object request,
            CancellationToken cancellationToken = default)
        {
            throw new NotSupportedException();
        }

        public Task<object?> Send(object request, CancellationToken cancellationToken = default)
        {
            LastRequest = request;

            if (_exception is not null)
            {
                throw _exception;
            }

            return Task.FromResult(_response);
        }
    }
}
