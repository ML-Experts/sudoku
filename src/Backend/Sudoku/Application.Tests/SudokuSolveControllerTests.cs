using FluentValidation;
using FluentValidation.Results;
using MediatR;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging.Abstractions;
using Sudoku.Application.SudokuSolve;
using Sudoku.Controllers;
using Sudoku.Contracts;

namespace Application.Tests;

public sealed class SudokuSolveControllerTests
{
    [Fact]
    public async Task CancelAsync_ReturnsAccepted_WhenCancellationIsAccepted()
    {
        var controller = CreateController(new StubSender(new CancelSolveSessionCommandResultDto(
            Status: "cancelling",
            RequestDisposition: "accepted")));

        var result = await controller.CancelAsync("solve-active", CancellationToken.None);

        var acceptedResult = Assert.IsType<ObjectResult>(result);
        Assert.Equal(StatusCodes.Status202Accepted, acceptedResult.StatusCode);

        var response = Assert.IsType<CancelSolveSessionApiResponse>(acceptedResult.Value);
        Assert.Equal("cancelling", response.Status);
        Assert.Equal("accepted", response.RequestDisposition);
    }

    [Fact]
    public async Task CancelAsync_ReturnsBadRequest_WhenSolveSessionIdIsInvalid()
    {
        var validationException = new ValidationException(
        [
            new ValidationFailure(nameof(CancelSolveSessionCommand.SolveSessionId), "Pole solveSessionId jest wymagane.")
            {
                ErrorCode = CancelSolveSessionErrorTypes.InvalidSolveSessionId
            }
        ]);
        var controller = CreateController(new StubSender(validationException));

        var result = await controller.CancelAsync(" ", CancellationToken.None);

        var objectResult = Assert.IsType<ObjectResult>(result);
        Assert.Equal(StatusCodes.Status400BadRequest, objectResult.StatusCode);

        var response = Assert.IsType<ErrorApiResponse>(objectResult.Value);
        Assert.Equal(CancelSolveSessionErrorTypes.InvalidSolveSessionId, response.ErrorType);
    }

    [Fact]
    public async Task CancelAsync_ReturnsInternalServerError_WhenPersistenceFails()
    {
        var controller = CreateController(new StubSender(new SolveSessionCancelPersistenceException("write failed")));

        var result = await controller.CancelAsync("solve-active", CancellationToken.None);

        var objectResult = Assert.IsType<ObjectResult>(result);
        Assert.Equal(StatusCodes.Status500InternalServerError, objectResult.StatusCode);

        var response = Assert.IsType<ErrorApiResponse>(objectResult.Value);
        Assert.Equal(CancelSolveSessionErrorTypes.SolveSessionCancelPersistenceFailed, response.ErrorType);
    }

    [Fact]
    public async Task CancelAsync_ReturnsInternalServerError_WhenInvariantViolationOccurs()
    {
        var controller = CreateController(new StubSender(new InvalidOperationException("broken invariant")));

        var result = await controller.CancelAsync("solve-active", CancellationToken.None);

        var objectResult = Assert.IsType<ObjectResult>(result);
        Assert.Equal(StatusCodes.Status500InternalServerError, objectResult.StatusCode);

        var response = Assert.IsType<ErrorApiResponse>(objectResult.Value);
        Assert.Equal(CancelSolveSessionErrorTypes.SolveSessionCancelInvariantViolation, response.ErrorType);
    }

    [Fact]
    public async Task GetActiveAsync_ReturnsOk_WhenActiveSessionExists()
    {
        var controller = CreateController(new StubSender(new GetActiveSolveSessionQueryResultDto(
            HasActiveSession: true,
            Session: new ActiveSolveSessionDto(
                SolveSessionId: "solve-active",
                Status: "running",
                ProgressChannelUrl: "/ws/sudoku/solving/solve-active"))));

        var result = await controller.GetActiveAsync(CancellationToken.None);

        var okResult = Assert.IsType<OkObjectResult>(result);
        var response = Assert.IsType<SolveSessionApiResponse>(okResult.Value);
        Assert.Equal("solve-active", response.SolveSessionId);
        Assert.Equal("running", response.Status);
        Assert.Equal("/ws/sudoku/solving/solve-active", response.ProgressChannelUrl);
    }

    [Fact]
    public async Task GetActiveAsync_ReturnsNoContent_WhenActiveSessionDoesNotExist()
    {
        var controller = CreateController(new StubSender(new GetActiveSolveSessionQueryResultDto(
            HasActiveSession: false,
            Session: null)));

        var result = await controller.GetActiveAsync(CancellationToken.None);

        Assert.IsType<NoContentResult>(result);
    }

    [Fact]
    public async Task GetActiveAsync_ReturnsInternalServerError_WhenInvariantViolationOccurs()
    {
        var controller = CreateController(new StubSender(new InvalidOperationException("broken invariant")));

        var result = await controller.GetActiveAsync(CancellationToken.None);

        var objectResult = Assert.IsType<ObjectResult>(result);
        Assert.Equal(StatusCodes.Status500InternalServerError, objectResult.StatusCode);

        var response = Assert.IsType<ErrorApiResponse>(objectResult.Value);
        Assert.Equal(GetActiveSolveSessionErrorTypes.InvariantViolation, response.ErrorType);
    }

    [Fact]
    public async Task GetActiveAsync_ReturnsInternalServerError_WhenReadFails()
    {
        var controller = CreateController(new StubSender(new IOException("storage read failed")));

        var result = await controller.GetActiveAsync(CancellationToken.None);

        var objectResult = Assert.IsType<ObjectResult>(result);
        Assert.Equal(StatusCodes.Status500InternalServerError, objectResult.StatusCode);

        var response = Assert.IsType<ErrorApiResponse>(objectResult.Value);
        Assert.Equal(GetActiveSolveSessionErrorTypes.ReadFailed, response.ErrorType);
    }

    private static SudokuSolveController CreateController(ISender sender)
    {
        return new SudokuSolveController(
            sender,
            NullLogger<SudokuSolveController>.Instance);
    }

    private sealed class StubSender : ISender
    {
        private readonly object? _response;
        private readonly Exception? _exception;

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
            if (_exception is not null)
            {
                throw _exception;
            }

            return Task.FromResult((TResponse)_response!);
        }

        public Task Send<TRequest>(TRequest request, CancellationToken cancellationToken = default)
            where TRequest : IRequest
        {
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
            if (_exception is not null)
            {
                throw _exception;
            }

            return Task.FromResult(_response);
        }
    }
}
