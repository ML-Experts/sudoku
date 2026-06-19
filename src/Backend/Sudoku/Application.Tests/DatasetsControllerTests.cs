using FluentValidation;
using FluentValidation.Results;
using MediatR;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging.Abstractions;
using Sudoku.Application.Datasets;
using Sudoku.Controllers;
using Sudoku.Contracts;

namespace Application.Tests;

public sealed class DatasetsControllerTests
{
    [Fact]
    public async Task ListPreparationsAsync_ReturnsOkAndMapsResponse()
    {
        var sender = new StubSender(new ListDatasetPreparationsQueryResultDto(
            Items:
            [
                new DatasetPreparationListItemDto(
                    PreparationName: "preparation-002",
                    CreatedAtUtc: DateTimeOffset.Parse("2026-06-19T19:05:44Z"),
                    Status: "running",
                    BoardSourcesCount: 2,
                    DigitSourcesCount: 0),
                new DatasetPreparationListItemDto(
                    PreparationName: "preparation-001",
                    CreatedAtUtc: DateTimeOffset.Parse("2026-06-19T18:42:11Z"),
                    Status: "completed",
                    BoardSourcesCount: 1,
                    DigitSourcesCount: 1)
            ],
            TotalCount: 2));
        var controller = CreateController(sender);

        var result = await controller.ListPreparationsAsync(CancellationToken.None);

        var okResult = Assert.IsType<OkObjectResult>(result);
        var query = Assert.IsType<ListDatasetPreparationsQuery>(sender.LastRequest);
        Assert.NotNull(query);

        var payload = Assert.IsType<DatasetPreparationsListApiResponse>(okResult.Value);
        Assert.Equal(2, payload.TotalCount);
        Assert.Collection(
            payload.Items,
            item =>
            {
                Assert.Equal("preparation-002", item.PreparationName);
                Assert.Equal("running", item.Status);
                Assert.Equal(2, item.BoardSourcesCount);
                Assert.Equal(0, item.DigitSourcesCount);
            },
            item =>
            {
                Assert.Equal("preparation-001", item.PreparationName);
                Assert.Equal("completed", item.Status);
                Assert.Equal(1, item.BoardSourcesCount);
                Assert.Equal(1, item.DigitSourcesCount);
            });
    }

    [Fact]
    public async Task ListPreparationsAsync_ReturnsInternalServerError_WhenReadFails()
    {
        var sender = new StubSender(new IOException("read failed"));
        var controller = CreateController(sender);

        var result = await controller.ListPreparationsAsync(CancellationToken.None);

        var objectResult = Assert.IsType<ObjectResult>(result);
        Assert.Equal(StatusCodes.Status500InternalServerError, objectResult.StatusCode);

        var payload = Assert.IsType<ErrorApiResponse>(objectResult.Value);
        Assert.Equal(ListDatasetPreparationsErrorTypes.ReadFailed, payload.ErrorType);
    }

    [Fact]
    public async Task CreatePreparationAsync_ReturnsAcceptedAndMapsCommand()
    {
        var sender = new StubSender(new CreateDatasetPreparationCommandResultDto(
            PreparationName: "preparation-001",
            CreatedAtUtc: DateTimeOffset.Parse("2026-06-19T18:42:11Z"),
            Status: "queued",
            Sources:
            [
                new DatasetPreparationSourceReportDto("v1_training", "board", 0, 0, 0)
            ],
            Warnings: []));
        var controller = CreateController(sender);

        var result = await controller.CreatePreparationAsync(
            new CreateDatasetPreparationApiEntry(
                PreparationName: "preparation-001",
                Sources: [new CreateDatasetPreparationSourceApiEntry("v1_training", "board")]),
            CancellationToken.None);

        var acceptedResult = Assert.IsType<ObjectResult>(result);
        Assert.Equal(StatusCodes.Status202Accepted, acceptedResult.StatusCode);

        var command = Assert.IsType<CreateDatasetPreparationCommand>(sender.LastRequest);
        Assert.Equal("preparation-001", command.PreparationName);
        Assert.Single(command.Sources!);
        Assert.Equal("v1_training", command.Sources![0].Name);
        Assert.Equal("board", command.Sources[0].Type);

        var payload = Assert.IsType<DatasetPreparationApiResponse>(acceptedResult.Value);
        Assert.Equal("queued", payload.Status);
        Assert.Single(payload.Sources);
        Assert.Equal(0, payload.Sources[0].PreparedItemsCount);
    }

    [Fact]
    public async Task CreatePreparationAsync_ReturnsBadRequest_WhenValidationFails()
    {
        var sender = new StubSender(new ValidationException([
            new ValidationFailure("PreparationName", "Pole 'preparationName' jest wymagane.")
            {
                ErrorCode = CreateDatasetPreparationErrorTypes.InvalidRequest
            }
        ]));
        var controller = CreateController(sender);

        var result = await controller.CreatePreparationAsync(
            new CreateDatasetPreparationApiEntry(
                PreparationName: null,
                Sources: [new CreateDatasetPreparationSourceApiEntry("v1_training", "board")]),
            CancellationToken.None);

        var badRequestResult = Assert.IsType<ObjectResult>(result);
        Assert.Equal(StatusCodes.Status400BadRequest, badRequestResult.StatusCode);

        var payload = Assert.IsType<ErrorApiResponse>(badRequestResult.Value);
        Assert.Equal(CreateDatasetPreparationErrorTypes.InvalidRequest, payload.ErrorType);
    }

    [Fact]
    public async Task CreatePreparationAsync_ReturnsNotFound_WhenSourceIsMissing()
    {
        var sender = new StubSender(new RawDatasetNotFoundException("Źródło zniknęło."));
        var controller = CreateController(sender);

        var result = await controller.CreatePreparationAsync(
            new CreateDatasetPreparationApiEntry(
                PreparationName: "preparation-001",
                Sources: [new CreateDatasetPreparationSourceApiEntry("v1_training", "board")]),
            CancellationToken.None);

        var notFoundResult = Assert.IsType<NotFoundObjectResult>(result);
        Assert.Equal(StatusCodes.Status404NotFound, notFoundResult.StatusCode);
    }

    [Fact]
    public async Task GetPreparationByNameAsync_ReturnsOkAndMapsResponse()
    {
        var sender = new StubSender(new GetDatasetPreparationDetailsQueryResultDto(
            PreparationName: "preparation-001",
            CreatedAtUtc: DateTimeOffset.Parse("2026-06-19T18:42:11Z"),
            Status: "completed",
            Sources:
            [
                new DatasetPreparationSourceReportDto("v1_training", "board", 24, 0, 0),
                new DatasetPreparationSourceReportDto("mnist_train", "digit", 110, 0, 0)
            ],
            Warnings: ["preparation_cleanup_partial"]));
        var controller = CreateController(sender);

        var result = await controller.GetPreparationByNameAsync("preparation-001", CancellationToken.None);

        var okResult = Assert.IsType<OkObjectResult>(result);
        var query = Assert.IsType<GetDatasetPreparationDetailsQuery>(sender.LastRequest);
        Assert.Equal("preparation-001", query.PreparationName);

        var payload = Assert.IsType<DatasetPreparationApiResponse>(okResult.Value);
        Assert.Equal("preparation-001", payload.PreparationName);
        Assert.Equal("completed", payload.Status);
        Assert.Collection(
            payload.Sources,
            source =>
            {
                Assert.Equal("v1_training", source.Name);
                Assert.Equal("board", source.Type);
                Assert.Equal(24, source.PreparedItemsCount);
            },
            source =>
            {
                Assert.Equal("mnist_train", source.Name);
                Assert.Equal("digit", source.Type);
                Assert.Equal(110, source.PreparedItemsCount);
            });
        Assert.Equal(["preparation_cleanup_partial"], payload.Warnings);
    }

    [Fact]
    public async Task GetPreparationByNameAsync_ReturnsBadRequest_WhenValidationFails()
    {
        var sender = new StubSender(new ValidationException([
            new ValidationFailure(nameof(GetDatasetPreparationDetailsQuery.PreparationName), "Pole 'preparationName' jest wymagane.")
            {
                ErrorCode = GetDatasetPreparationDetailsErrorTypes.InvalidDatasetPreparationName
            }
        ]));
        var controller = CreateController(sender);

        var result = await controller.GetPreparationByNameAsync(null, CancellationToken.None);

        var badRequestResult = Assert.IsType<ObjectResult>(result);
        Assert.Equal(StatusCodes.Status400BadRequest, badRequestResult.StatusCode);

        var payload = Assert.IsType<ErrorApiResponse>(badRequestResult.Value);
        Assert.Equal(GetDatasetPreparationDetailsErrorTypes.InvalidDatasetPreparationName, payload.ErrorType);
    }

    [Fact]
    public async Task GetPreparationByNameAsync_ReturnsNotFound_WhenPreparationDoesNotExist()
    {
        var sender = new StubSender(new DatasetPreparationNotFoundException("missing"));
        var controller = CreateController(sender);

        var result = await controller.GetPreparationByNameAsync("missing", CancellationToken.None);

        var notFoundResult = Assert.IsType<NotFoundObjectResult>(result);
        Assert.Equal(StatusCodes.Status404NotFound, notFoundResult.StatusCode);

        var payload = Assert.IsType<ErrorApiResponse>(notFoundResult.Value);
        Assert.Equal(GetDatasetPreparationDetailsErrorTypes.DatasetPreparationNotFound, payload.ErrorType);
    }

    [Fact]
    public async Task GetPreparationByNameAsync_ReturnsInternalServerError_WhenReadFails()
    {
        var sender = new StubSender(new InvalidDataException("broken metadata"));
        var controller = CreateController(sender);

        var result = await controller.GetPreparationByNameAsync("preparation-001", CancellationToken.None);

        var objectResult = Assert.IsType<ObjectResult>(result);
        Assert.Equal(StatusCodes.Status500InternalServerError, objectResult.StatusCode);

        var payload = Assert.IsType<ErrorApiResponse>(objectResult.Value);
        Assert.Equal(GetDatasetPreparationDetailsErrorTypes.DatasetPreparationReadFailed, payload.ErrorType);
    }

    private static DatasetsController CreateController(StubSender sender)
    {
        return new DatasetsController(sender, NullLogger<DatasetsController>.Instance);
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
