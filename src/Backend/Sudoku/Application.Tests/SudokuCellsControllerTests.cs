using MediatR;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging.Abstractions;
using Sudoku.Application.Sudoku;
using Sudoku.Controllers;
using Sudoku.Contracts;

namespace Application.Tests;

public sealed class SudokuCellsControllerTests
{
    [Fact]
    public async Task InferAsync_PassesEmptyCellParametersToCommand()
    {
        var sender = new StubSender(new InferSudokuCellDigitCommandResultDto(7));
        var controller = CreateController(sender);

        var result = await controller.InferAsync(
            new DigitInferenceApiEntry
            {
                Image = new ImageApiEntry("image/png", Convert.ToBase64String([1, 2, 3])),
                EmptyCellDarkPixelRatioThreshold = 0.02,
                EmptyCellInnerMarginRatio = 0.12,
                CenterAreaRatio = 0.5,
                MinComponentAreaRatio = 0.055,
                LineArtifactMinSpanRatio = 0.4,
                LineArtifactMaxThicknessRatio = 0.08
            },
            CancellationToken.None);

        var okResult = Assert.IsType<OkObjectResult>(result);
        Assert.Equal(StatusCodes.Status200OK, okResult.StatusCode);

        var command = Assert.IsType<InferSudokuCellDigitCommand>(sender.LastRequest);
        Assert.Equal(0.02, command.EmptyCellDarkPixelRatioThreshold);
        Assert.Equal(0.12, command.EmptyCellInnerMarginRatio);
    }

    private static SudokuCellsController CreateController(ISender sender)
    {
        return new SudokuCellsController(
            sender,
            NullLogger<SudokuCellsController>.Instance);
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
