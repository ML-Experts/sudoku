using FluentValidation;
using FluentValidation.Results;
using MediatR;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging.Abstractions;
using Sudoku.Application.Datasets;
using Sudoku.Application.Storage;
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

    [Fact]
    public async Task GetPreparationBoardFoldersAsync_ReturnsOkAndMapsResponse()
    {
        var sender = new StubSender(new GetDatasetPreparationFoldersQueryResultDto(
            PreparationName: "preparation-001",
            Type: "board",
            Items: ["v1_training", "v2_training"],
            TotalCount: 2));
        var controller = CreateController(sender);

        var result = await controller.GetPreparationBoardFoldersAsync("preparation-001", CancellationToken.None);

        var okResult = Assert.IsType<OkObjectResult>(result);
        var query = Assert.IsType<GetDatasetPreparationFoldersQuery>(sender.LastRequest);
        Assert.Equal("preparation-001", query.PreparationName);
        Assert.Equal("board", query.Type);

        var payload = Assert.IsType<DatasetPreparationFoldersApiResponse>(okResult.Value);
        Assert.Equal("preparation-001", payload.PreparationName);
        Assert.Equal("board", payload.Type);
        Assert.Equal(2, payload.TotalCount);
        Assert.Equal(["v1_training", "v2_training"], payload.Items);
    }

    [Fact]
    public async Task GetPreparationBoardFoldersAsync_ReturnsBadRequest_WhenValidationFails()
    {
        var sender = new StubSender(new ValidationException([
            new ValidationFailure(nameof(GetDatasetPreparationFoldersQuery.PreparationName), "Pole 'preparationName' jest wymagane.")
            {
                ErrorCode = GetDatasetPreparationFoldersErrorTypes.InvalidDatasetPreparationName
            }
        ]));
        var controller = CreateController(sender);

        var result = await controller.GetPreparationBoardFoldersAsync(null, CancellationToken.None);

        var objectResult = Assert.IsType<ObjectResult>(result);
        Assert.Equal(StatusCodes.Status400BadRequest, objectResult.StatusCode);

        var payload = Assert.IsType<ErrorApiResponse>(objectResult.Value);
        Assert.Equal(GetDatasetPreparationFoldersErrorTypes.InvalidDatasetPreparationName, payload.ErrorType);
    }

    [Fact]
    public async Task GetPreparationBoardFoldersAsync_ReturnsNotFound_WhenPreparationDoesNotExist()
    {
        var sender = new StubSender(new DatasetPreparationNotFoundException("missing"));
        var controller = CreateController(sender);

        var result = await controller.GetPreparationBoardFoldersAsync("missing", CancellationToken.None);

        var notFoundResult = Assert.IsType<NotFoundObjectResult>(result);
        Assert.Equal(StatusCodes.Status404NotFound, notFoundResult.StatusCode);

        var payload = Assert.IsType<ErrorApiResponse>(notFoundResult.Value);
        Assert.Equal(GetDatasetPreparationFoldersErrorTypes.DatasetPreparationNotFound, payload.ErrorType);
    }

    [Fact]
    public async Task GetPreparationBoardFoldersAsync_ReturnsConflict_WhenArtifactsAreNotReady()
    {
        var sender = new StubSender(new DatasetPreparationArtifactsNotReadyException("preparation-001", "running"));
        var controller = CreateController(sender);

        var result = await controller.GetPreparationBoardFoldersAsync("preparation-001", CancellationToken.None);

        var conflictResult = Assert.IsType<ConflictObjectResult>(result);
        Assert.Equal(StatusCodes.Status409Conflict, conflictResult.StatusCode);

        var payload = Assert.IsType<ErrorApiResponse>(conflictResult.Value);
        Assert.Equal(GetDatasetPreparationFoldersErrorTypes.DatasetPreparationArtifactsNotReady, payload.ErrorType);
    }

    [Fact]
    public async Task GetPreparationBoardFoldersAsync_ReturnsInternalServerError_WhenReadFails()
    {
        var sender = new StubSender(new InvalidDataException("broken manifest"));
        var controller = CreateController(sender);

        var result = await controller.GetPreparationBoardFoldersAsync("preparation-001", CancellationToken.None);

        var objectResult = Assert.IsType<ObjectResult>(result);
        Assert.Equal(StatusCodes.Status500InternalServerError, objectResult.StatusCode);

        var payload = Assert.IsType<ErrorApiResponse>(objectResult.Value);
        Assert.Equal(GetDatasetPreparationFoldersErrorTypes.DatasetPreparationFoldersReadFailed, payload.ErrorType);
    }

    [Fact]
    public async Task GetPreparationDigitFoldersAsync_ReturnsOkAndMapsResponse()
    {
        var sender = new StubSender(new GetDatasetPreparationFoldersQueryResultDto(
            PreparationName: "preparation-001",
            Type: "digit",
            Items: ["mnist_train", "mnist_test"],
            TotalCount: 2));
        var controller = CreateController(sender);

        var result = await controller.GetPreparationDigitFoldersAsync("preparation-001", CancellationToken.None);

        var okResult = Assert.IsType<OkObjectResult>(result);
        var query = Assert.IsType<GetDatasetPreparationFoldersQuery>(sender.LastRequest);
        Assert.Equal("preparation-001", query.PreparationName);
        Assert.Equal("digit", query.Type);

        var payload = Assert.IsType<DatasetPreparationFoldersApiResponse>(okResult.Value);
        Assert.Equal("preparation-001", payload.PreparationName);
        Assert.Equal("digit", payload.Type);
        Assert.Equal(2, payload.TotalCount);
        Assert.Equal(["mnist_train", "mnist_test"], payload.Items);
    }

    [Fact]
    public async Task GetPreparationDigitFoldersAsync_ReturnsBadRequest_WhenValidationFails()
    {
        var sender = new StubSender(new ValidationException([
            new ValidationFailure(nameof(GetDatasetPreparationFoldersQuery.PreparationName), "Pole 'preparationName' jest wymagane.")
            {
                ErrorCode = GetDatasetPreparationFoldersErrorTypes.InvalidDatasetPreparationName
            }
        ]));
        var controller = CreateController(sender);

        var result = await controller.GetPreparationDigitFoldersAsync(null, CancellationToken.None);

        var objectResult = Assert.IsType<ObjectResult>(result);
        Assert.Equal(StatusCodes.Status400BadRequest, objectResult.StatusCode);

        var payload = Assert.IsType<ErrorApiResponse>(objectResult.Value);
        Assert.Equal(GetDatasetPreparationFoldersErrorTypes.InvalidDatasetPreparationName, payload.ErrorType);
    }

    [Fact]
    public async Task GetPreparationDigitFoldersAsync_ReturnsNotFound_WhenPreparationDoesNotExist()
    {
        var sender = new StubSender(new DatasetPreparationNotFoundException("missing"));
        var controller = CreateController(sender);

        var result = await controller.GetPreparationDigitFoldersAsync("missing", CancellationToken.None);

        var notFoundResult = Assert.IsType<NotFoundObjectResult>(result);
        Assert.Equal(StatusCodes.Status404NotFound, notFoundResult.StatusCode);

        var payload = Assert.IsType<ErrorApiResponse>(notFoundResult.Value);
        Assert.Equal(GetDatasetPreparationFoldersErrorTypes.DatasetPreparationNotFound, payload.ErrorType);
    }

    [Fact]
    public async Task GetPreparationDigitFoldersAsync_ReturnsConflict_WhenArtifactsAreNotReady()
    {
        var sender = new StubSender(new DatasetPreparationArtifactsNotReadyException("preparation-001", "running"));
        var controller = CreateController(sender);

        var result = await controller.GetPreparationDigitFoldersAsync("preparation-001", CancellationToken.None);

        var conflictResult = Assert.IsType<ConflictObjectResult>(result);
        Assert.Equal(StatusCodes.Status409Conflict, conflictResult.StatusCode);

        var payload = Assert.IsType<ErrorApiResponse>(conflictResult.Value);
        Assert.Equal(GetDatasetPreparationFoldersErrorTypes.DatasetPreparationArtifactsNotReady, payload.ErrorType);
    }

    [Fact]
    public async Task GetPreparationDigitFoldersAsync_ReturnsInternalServerError_WhenReadFails()
    {
        var sender = new StubSender(new InvalidDataException("broken manifest"));
        var controller = CreateController(sender);

        var result = await controller.GetPreparationDigitFoldersAsync("preparation-001", CancellationToken.None);

        var objectResult = Assert.IsType<ObjectResult>(result);
        Assert.Equal(StatusCodes.Status500InternalServerError, objectResult.StatusCode);

        var payload = Assert.IsType<ErrorApiResponse>(objectResult.Value);
        Assert.Equal(GetDatasetPreparationFoldersErrorTypes.DatasetPreparationFoldersReadFailed, payload.ErrorType);
    }

    [Fact]
    public async Task GetPreparationBoardFilesAsync_ReturnsOkAndMapsResponse()
    {
        var sender = new StubSender(new GetDatasetPreparationBoardFilesQueryResultDto(
            PreparationName: "preparation-001",
            SourceName: "v1_training",
            Items:
            [
                new DatasetPreparationBoardFileListItemDto("Image1"),
                new DatasetPreparationBoardFileListItemDto("Image 2")
            ],
            Page: 2,
            PageSize: 2,
            TotalCount: 5));
        var controller = CreateController(sender);

        var result = await controller.GetPreparationBoardFilesAsync(
            "preparation-001",
            "v1_training",
            2,
            2,
            CancellationToken.None);

        var okResult = Assert.IsType<OkObjectResult>(result);
        var query = Assert.IsType<GetDatasetPreparationBoardFilesQuery>(sender.LastRequest);
        Assert.Equal("preparation-001", query.PreparationName);
        Assert.Equal("v1_training", query.SourceName);
        Assert.Equal(2, query.Page);
        Assert.Equal(2, query.PageSize);

        var payload = Assert.IsType<DatasetPreparationBoardFilesApiResponse>(okResult.Value);
        Assert.Equal("preparation-001", payload.PreparationName);
        Assert.Equal("v1_training", payload.SourceName);
        Assert.Equal(2, payload.Page);
        Assert.Equal(2, payload.PageSize);
        Assert.Equal(5, payload.TotalCount);
        Assert.Collection(
            payload.Items,
            item =>
            {
                Assert.Equal("Image1", item.BoardFolderName);
                Assert.Equal("/api/datasets/preparations/preparation-001/board/v1_training/files/Image1/image", item.ImageEndpoint);
            },
            item =>
            {
                Assert.Equal("Image 2", item.BoardFolderName);
                Assert.Equal("/api/datasets/preparations/preparation-001/board/v1_training/files/Image%202/image", item.ImageEndpoint);
            });
    }

    [Fact]
    public async Task GetPreparationBoardFilesAsync_ReturnsBadRequest_WhenValidationFails()
    {
        var sender = new StubSender(new ValidationException([
            new ValidationFailure(nameof(GetDatasetPreparationBoardFilesQuery.SourceName), "Pole 'sourceName' jest wymagane.")
            {
                ErrorCode = GetDatasetPreparationBoardFilesErrorTypes.InvalidDatasetPreparationSourceName
            }
        ]));
        var controller = CreateController(sender);

        var result = await controller.GetPreparationBoardFilesAsync(
            "preparation-001",
            null,
            1,
            50,
            CancellationToken.None);

        var objectResult = Assert.IsType<ObjectResult>(result);
        Assert.Equal(StatusCodes.Status400BadRequest, objectResult.StatusCode);

        var payload = Assert.IsType<ErrorApiResponse>(objectResult.Value);
        Assert.Equal(GetDatasetPreparationBoardFilesErrorTypes.InvalidDatasetPreparationSourceName, payload.ErrorType);
    }

    [Fact]
    public async Task GetPreparationBoardFilesAsync_ReturnsNotFound_WhenPreparationDoesNotExist()
    {
        var sender = new StubSender(new DatasetPreparationNotFoundException("missing"));
        var controller = CreateController(sender);

        var result = await controller.GetPreparationBoardFilesAsync(
            "missing",
            "v1_training",
            1,
            50,
            CancellationToken.None);

        var notFoundResult = Assert.IsType<NotFoundObjectResult>(result);
        Assert.Equal(StatusCodes.Status404NotFound, notFoundResult.StatusCode);

        var payload = Assert.IsType<ErrorApiResponse>(notFoundResult.Value);
        Assert.Equal(GetDatasetPreparationBoardFilesErrorTypes.DatasetPreparationNotFound, payload.ErrorType);
    }

    [Fact]
    public async Task GetPreparationBoardFilesAsync_ReturnsNotFound_WhenSourceDoesNotExist()
    {
        var sender = new StubSender(new DatasetPreparationSourceNotFoundException("preparation-001", "missing-source"));
        var controller = CreateController(sender);

        var result = await controller.GetPreparationBoardFilesAsync(
            "preparation-001",
            "missing-source",
            1,
            50,
            CancellationToken.None);

        var notFoundResult = Assert.IsType<NotFoundObjectResult>(result);
        Assert.Equal(StatusCodes.Status404NotFound, notFoundResult.StatusCode);

        var payload = Assert.IsType<ErrorApiResponse>(notFoundResult.Value);
        Assert.Equal(GetDatasetPreparationBoardFilesErrorTypes.DatasetPreparationSourceNotFound, payload.ErrorType);
    }

    [Fact]
    public async Task GetPreparationBoardFilesAsync_ReturnsConflict_WhenArtifactsAreNotReady()
    {
        var sender = new StubSender(new DatasetPreparationArtifactsNotReadyException("preparation-001", "running"));
        var controller = CreateController(sender);

        var result = await controller.GetPreparationBoardFilesAsync(
            "preparation-001",
            "v1_training",
            1,
            50,
            CancellationToken.None);

        var conflictResult = Assert.IsType<ConflictObjectResult>(result);
        Assert.Equal(StatusCodes.Status409Conflict, conflictResult.StatusCode);

        var payload = Assert.IsType<ErrorApiResponse>(conflictResult.Value);
        Assert.Equal(GetDatasetPreparationBoardFilesErrorTypes.DatasetPreparationArtifactsNotReady, payload.ErrorType);
    }

    [Fact]
    public async Task GetPreparationBoardFilesAsync_ReturnsInternalServerError_WhenReadFails()
    {
        var sender = new StubSender(new InvalidDataException("broken file manifest"));
        var controller = CreateController(sender);

        var result = await controller.GetPreparationBoardFilesAsync(
            "preparation-001",
            "v1_training",
            1,
            50,
            CancellationToken.None);

        var objectResult = Assert.IsType<ObjectResult>(result);
        Assert.Equal(StatusCodes.Status500InternalServerError, objectResult.StatusCode);

        var payload = Assert.IsType<ErrorApiResponse>(objectResult.Value);
        Assert.Equal(GetDatasetPreparationBoardFilesErrorTypes.DatasetPreparationBoardFilesReadFailed, payload.ErrorType);
    }

    [Fact]
    public async Task GetPreparationBoardImageAsync_ReturnsOkAndMapsResponse()
    {
        var sender = new StubSender(new GetDatasetPreparationBoardImageQueryResultDto(
            MimeType: "image/png",
            Base64: "AQID"));
        var controller = CreateController(sender);

        var result = await controller.GetPreparationBoardImageAsync(
            "preparation-001",
            "v1_training",
            "Image 1",
            CancellationToken.None);

        var okResult = Assert.IsType<OkObjectResult>(result);
        var query = Assert.IsType<GetDatasetPreparationBoardImageQuery>(sender.LastRequest);
        Assert.Equal("preparation-001", query.PreparationName);
        Assert.Equal("v1_training", query.SourceName);
        Assert.Equal("Image 1", query.BoardFolderName);

        var payload = Assert.IsType<ImageApiResponse>(okResult.Value);
        Assert.Equal("image/png", payload.MimeType);
        Assert.Equal("AQID", payload.Base64);
    }

    [Fact]
    public async Task GetPreparationBoardImageAsync_ReturnsBadRequest_WhenValidationFails()
    {
        var sender = new StubSender(new ValidationException([
            new ValidationFailure(nameof(GetDatasetPreparationBoardImageQuery.BoardFolderName), "Pole 'boardFolderName' jest wymagane.")
            {
                ErrorCode = GetDatasetPreparationBoardImageErrorTypes.InvalidDatasetPreparationBoardFolderName
            }
        ]));
        var controller = CreateController(sender);

        var result = await controller.GetPreparationBoardImageAsync(
            "preparation-001",
            "v1_training",
            null,
            CancellationToken.None);

        var objectResult = Assert.IsType<ObjectResult>(result);
        Assert.Equal(StatusCodes.Status400BadRequest, objectResult.StatusCode);

        var payload = Assert.IsType<ErrorApiResponse>(objectResult.Value);
        Assert.Equal(GetDatasetPreparationBoardImageErrorTypes.InvalidDatasetPreparationBoardFolderName, payload.ErrorType);
    }

    [Fact]
    public async Task GetPreparationBoardImageAsync_ReturnsNotFound_WhenPreparationDoesNotExist()
    {
        var sender = new StubSender(new DatasetPreparationNotFoundException("missing"));
        var controller = CreateController(sender);

        var result = await controller.GetPreparationBoardImageAsync(
            "missing",
            "v1_training",
            "Image1",
            CancellationToken.None);

        var notFoundResult = Assert.IsType<NotFoundObjectResult>(result);
        Assert.Equal(StatusCodes.Status404NotFound, notFoundResult.StatusCode);

        var payload = Assert.IsType<ErrorApiResponse>(notFoundResult.Value);
        Assert.Equal(GetDatasetPreparationBoardImageErrorTypes.DatasetPreparationNotFound, payload.ErrorType);
    }

    [Fact]
    public async Task GetPreparationBoardImageAsync_ReturnsNotFound_WhenSourceDoesNotExist()
    {
        var sender = new StubSender(new DatasetPreparationSourceNotFoundException("preparation-001", "missing-source"));
        var controller = CreateController(sender);

        var result = await controller.GetPreparationBoardImageAsync(
            "preparation-001",
            "missing-source",
            "Image1",
            CancellationToken.None);

        var notFoundResult = Assert.IsType<NotFoundObjectResult>(result);
        Assert.Equal(StatusCodes.Status404NotFound, notFoundResult.StatusCode);

        var payload = Assert.IsType<ErrorApiResponse>(notFoundResult.Value);
        Assert.Equal(GetDatasetPreparationBoardImageErrorTypes.DatasetPreparationSourceNotFound, payload.ErrorType);
    }

    [Fact]
    public async Task GetPreparationBoardImageAsync_ReturnsNotFound_WhenBoardFolderDoesNotExist()
    {
        var sender = new StubSender(new DatasetPreparationBoardFileNotFoundException("preparation-001", "v1_training", "Image404"));
        var controller = CreateController(sender);

        var result = await controller.GetPreparationBoardImageAsync(
            "preparation-001",
            "v1_training",
            "Image404",
            CancellationToken.None);

        var notFoundResult = Assert.IsType<NotFoundObjectResult>(result);
        Assert.Equal(StatusCodes.Status404NotFound, notFoundResult.StatusCode);

        var payload = Assert.IsType<ErrorApiResponse>(notFoundResult.Value);
        Assert.Equal(GetDatasetPreparationBoardImageErrorTypes.DatasetPreparationBoardFileNotFound, payload.ErrorType);
    }

    [Fact]
    public async Task GetPreparationBoardImageAsync_ReturnsConflict_WhenArtifactsAreNotReady()
    {
        var sender = new StubSender(new DatasetPreparationArtifactsNotReadyException("preparation-001", "running"));
        var controller = CreateController(sender);

        var result = await controller.GetPreparationBoardImageAsync(
            "preparation-001",
            "v1_training",
            "Image1",
            CancellationToken.None);

        var conflictResult = Assert.IsType<ConflictObjectResult>(result);
        Assert.Equal(StatusCodes.Status409Conflict, conflictResult.StatusCode);

        var payload = Assert.IsType<ErrorApiResponse>(conflictResult.Value);
        Assert.Equal(GetDatasetPreparationBoardImageErrorTypes.DatasetPreparationArtifactsNotReady, payload.ErrorType);
    }

    [Fact]
    public async Task GetPreparationBoardImageAsync_ReturnsInternalServerError_WhenReadFails()
    {
        var sender = new StubSender(new FileStorageItemNotFoundException("Wskazany plik nie istnieje."));
        var controller = CreateController(sender);

        var result = await controller.GetPreparationBoardImageAsync(
            "preparation-001",
            "v1_training",
            "Image1",
            CancellationToken.None);

        var objectResult = Assert.IsType<ObjectResult>(result);
        Assert.Equal(StatusCodes.Status500InternalServerError, objectResult.StatusCode);

        var payload = Assert.IsType<ErrorApiResponse>(objectResult.Value);
        Assert.Equal(GetDatasetPreparationBoardImageErrorTypes.DatasetPreparationBoardImageReadFailed, payload.ErrorType);
    }

    [Fact]
    public async Task DeletePreparationBoardFileAsync_ReturnsOkAndMapsResponse()
    {
        var sender = new StubSender(new DeleteDatasetPreparationBoardFileCommandResultDto(
            PreparationName: "preparation-001",
            SourceName: "v1_training",
            BoardFolderName: "Image 1",
            Deleted: true,
            RemainingItemsCount: 41));
        var controller = CreateController(sender);

        var result = await controller.DeletePreparationBoardFileAsync(
            "preparation-001",
            "v1_training",
            "Image 1",
            CancellationToken.None);

        var okResult = Assert.IsType<OkObjectResult>(result);
        var command = Assert.IsType<DeleteDatasetPreparationBoardFileCommand>(sender.LastRequest);
        Assert.Equal("preparation-001", command.PreparationName);
        Assert.Equal("v1_training", command.SourceName);
        Assert.Equal("Image 1", command.BoardFolderName);

        var payload = Assert.IsType<DeleteDatasetPreparationBoardFileApiResponse>(okResult.Value);
        Assert.Equal("preparation-001", payload.PreparationName);
        Assert.Equal("v1_training", payload.SourceName);
        Assert.Equal("Image 1", payload.BoardFolderName);
        Assert.True(payload.Deleted);
        Assert.Equal(41, payload.RemainingItemsCount);
    }

    [Fact]
    public async Task DeletePreparationBoardFileAsync_ReturnsBadRequest_WhenValidationFails()
    {
        var sender = new StubSender(new ValidationException([
            new ValidationFailure(nameof(DeleteDatasetPreparationBoardFileCommand.BoardFolderName), "Pole 'boardFolderName' jest wymagane.")
            {
                ErrorCode = DeleteDatasetPreparationBoardFileErrorTypes.InvalidDatasetPreparationBoardFolderName
            }
        ]));
        var controller = CreateController(sender);

        var result = await controller.DeletePreparationBoardFileAsync(
            "preparation-001",
            "v1_training",
            null,
            CancellationToken.None);

        var objectResult = Assert.IsType<ObjectResult>(result);
        Assert.Equal(StatusCodes.Status400BadRequest, objectResult.StatusCode);

        var payload = Assert.IsType<ErrorApiResponse>(objectResult.Value);
        Assert.Equal(DeleteDatasetPreparationBoardFileErrorTypes.InvalidDatasetPreparationBoardFolderName, payload.ErrorType);
    }

    [Fact]
    public async Task DeletePreparationBoardFileAsync_ReturnsNotFound_WhenPreparationDoesNotExist()
    {
        var sender = new StubSender(new DatasetPreparationNotFoundException("missing"));
        var controller = CreateController(sender);

        var result = await controller.DeletePreparationBoardFileAsync(
            "missing",
            "v1_training",
            "Image1",
            CancellationToken.None);

        var notFoundResult = Assert.IsType<NotFoundObjectResult>(result);
        Assert.Equal(StatusCodes.Status404NotFound, notFoundResult.StatusCode);

        var payload = Assert.IsType<ErrorApiResponse>(notFoundResult.Value);
        Assert.Equal(DeleteDatasetPreparationBoardFileErrorTypes.DatasetPreparationNotFound, payload.ErrorType);
    }

    [Fact]
    public async Task DeletePreparationBoardFileAsync_ReturnsNotFound_WhenSourceDoesNotExist()
    {
        var sender = new StubSender(new DatasetPreparationSourceNotFoundException("preparation-001", "missing-source"));
        var controller = CreateController(sender);

        var result = await controller.DeletePreparationBoardFileAsync(
            "preparation-001",
            "missing-source",
            "Image1",
            CancellationToken.None);

        var notFoundResult = Assert.IsType<NotFoundObjectResult>(result);
        Assert.Equal(StatusCodes.Status404NotFound, notFoundResult.StatusCode);

        var payload = Assert.IsType<ErrorApiResponse>(notFoundResult.Value);
        Assert.Equal(DeleteDatasetPreparationBoardFileErrorTypes.DatasetPreparationSourceNotFound, payload.ErrorType);
    }

    [Fact]
    public async Task DeletePreparationBoardFileAsync_ReturnsNotFound_WhenBoardFolderDoesNotExist()
    {
        var sender = new StubSender(new DatasetPreparationBoardFileNotFoundException("preparation-001", "v1_training", "Image404"));
        var controller = CreateController(sender);

        var result = await controller.DeletePreparationBoardFileAsync(
            "preparation-001",
            "v1_training",
            "Image404",
            CancellationToken.None);

        var notFoundResult = Assert.IsType<NotFoundObjectResult>(result);
        Assert.Equal(StatusCodes.Status404NotFound, notFoundResult.StatusCode);

        var payload = Assert.IsType<ErrorApiResponse>(notFoundResult.Value);
        Assert.Equal(DeleteDatasetPreparationBoardFileErrorTypes.DatasetPreparationBoardFileNotFound, payload.ErrorType);
    }

    [Fact]
    public async Task DeletePreparationBoardFileAsync_ReturnsConflict_WhenArtifactsAreNotReady()
    {
        var sender = new StubSender(new DatasetPreparationArtifactsNotReadyException("preparation-001", "running"));
        var controller = CreateController(sender);

        var result = await controller.DeletePreparationBoardFileAsync(
            "preparation-001",
            "v1_training",
            "Image1",
            CancellationToken.None);

        var conflictResult = Assert.IsType<ConflictObjectResult>(result);
        Assert.Equal(StatusCodes.Status409Conflict, conflictResult.StatusCode);

        var payload = Assert.IsType<ErrorApiResponse>(conflictResult.Value);
        Assert.Equal(DeleteDatasetPreparationBoardFileErrorTypes.DatasetPreparationArtifactsNotReady, payload.ErrorType);
    }

    [Fact]
    public async Task DeletePreparationBoardFileAsync_ReturnsInternalServerError_WhenDeleteFails()
    {
        var sender = new StubSender(new IOException("delete failed"));
        var controller = CreateController(sender);

        var result = await controller.DeletePreparationBoardFileAsync(
            "preparation-001",
            "v1_training",
            "Image1",
            CancellationToken.None);

        var objectResult = Assert.IsType<ObjectResult>(result);
        Assert.Equal(StatusCodes.Status500InternalServerError, objectResult.StatusCode);

        var payload = Assert.IsType<ErrorApiResponse>(objectResult.Value);
        Assert.Equal(DeleteDatasetPreparationBoardFileErrorTypes.DatasetPreparationBoardFileDeleteFailed, payload.ErrorType);
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
