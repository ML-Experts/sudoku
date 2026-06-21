using FluentValidation;
using FluentValidation.Results;
using MediatR;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Sudoku.Application.Examples;
using Sudoku.Application.Ml;
using Sudoku.Controllers;
using Sudoku.Contracts;

namespace Application.Tests;

public sealed class ExamplesControllerTests
{
    [Fact]
    public async Task PreprocessBoardInlineAsync_ReturnsOkAndMapsResponse()
    {
        var sender = new StubSender(new PreprocessBoardResultDto(
            MimeType: "image/png",
            Base64: "AQID"));
        var controller = CreateController(sender);

        var result = await controller.PreprocessBoardInlineAsync(
            new ImageApiEntry(
                MimeType: "image/jpeg",
                Base64: Convert.ToBase64String([1, 2, 3])),
            CancellationToken.None);

        var okResult = Assert.IsType<OkObjectResult>(result);
        var command = Assert.IsType<PreprocessInlineBoardCommand>(sender.LastRequest);
        Assert.Equal("image/jpeg", command.MimeType);
        Assert.Equal(Convert.ToBase64String([1, 2, 3]), command.Base64);

        var payload = Assert.IsType<ImageApiResponse>(okResult.Value);
        Assert.Equal("image/png", payload.MimeType);
        Assert.Equal("AQID", payload.Base64);
    }

    [Fact]
    public async Task PreprocessBoardInlineAsync_ReturnsBadRequest_WhenValidationFails()
    {
        var sender = new StubSender(new ValidationException([
            new ValidationFailure(nameof(PreprocessInlineBoardCommand.Base64), "Pole 'base64' jest wymagane.")
            {
                ErrorCode = PreprocessInlineBoardErrorTypes.InvalidRequest
            }
        ]));
        var controller = CreateController(sender);

        var result = await controller.PreprocessBoardInlineAsync(
            new ImageApiEntry(
                MimeType: "image/png",
                Base64: null),
            CancellationToken.None);

        var objectResult = Assert.IsType<ObjectResult>(result);
        Assert.Equal(StatusCodes.Status400BadRequest, objectResult.StatusCode);

        var payload = Assert.IsType<ErrorApiResponse>(objectResult.Value);
        Assert.Equal(PreprocessInlineBoardErrorTypes.InvalidRequest, payload.ErrorType);
    }

    [Fact]
    public async Task PreprocessBoardInlineAsync_ReturnsUnprocessableEntity_WhenMlOperationFails()
    {
        var sender = new StubSender(new MlOperationFailedException("board_not_found", "Nie wykryto planszy."));
        var controller = CreateController(sender);

        var result = await controller.PreprocessBoardInlineAsync(
            new ImageApiEntry(
                MimeType: "image/png",
                Base64: Convert.ToBase64String([1, 2, 3])),
            CancellationToken.None);

        var unprocessableResult = Assert.IsType<UnprocessableEntityObjectResult>(result);
        Assert.Equal(StatusCodes.Status422UnprocessableEntity, unprocessableResult.StatusCode);

        var payload = Assert.IsType<ErrorApiResponse>(unprocessableResult.Value);
        Assert.Equal("board_not_found", payload.ErrorType);
    }

    [Fact]
    public async Task PreprocessBoardInlineAsync_ReturnsServiceUnavailable_WhenMlIsUnavailable()
    {
        var sender = new StubSender(new MlServiceUnavailableException("Serwis ML jest niedostępny."));
        var controller = CreateController(sender);

        var result = await controller.PreprocessBoardInlineAsync(
            new ImageApiEntry(
                MimeType: "image/png",
                Base64: Convert.ToBase64String([1, 2, 3])),
            CancellationToken.None);

        var objectResult = Assert.IsType<ObjectResult>(result);
        Assert.Equal(StatusCodes.Status503ServiceUnavailable, objectResult.StatusCode);

        var payload = Assert.IsType<ErrorApiResponse>(objectResult.Value);
        Assert.Equal(PreprocessInlineBoardErrorTypes.MlUnavailable, payload.ErrorType);
    }

    [Fact]
    public async Task PreprocessBoardInlineAsync_ReturnsGatewayTimeout_WhenMlTimesOut()
    {
        var sender = new StubSender(new MlServiceTimeoutException("timeout"));
        var controller = CreateController(sender);

        var result = await controller.PreprocessBoardInlineAsync(
            new ImageApiEntry(
                MimeType: "image/png",
                Base64: Convert.ToBase64String([1, 2, 3])),
            CancellationToken.None);

        var objectResult = Assert.IsType<ObjectResult>(result);
        Assert.Equal(StatusCodes.Status504GatewayTimeout, objectResult.StatusCode);

        var payload = Assert.IsType<ErrorApiResponse>(objectResult.Value);
        Assert.Equal(PreprocessInlineBoardErrorTypes.MlTimeout, payload.ErrorType);
    }

    private static ExamplesController CreateController(StubSender sender)
    {
        return new ExamplesController(sender);
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
