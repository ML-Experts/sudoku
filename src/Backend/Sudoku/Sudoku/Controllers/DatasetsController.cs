using FluentValidation;
using MediatR;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using System.Text.Json;
using Sudoku.Application.Datasets;
using Sudoku.Application.Ml;
using Sudoku.Application.Storage;
using Sudoku.Contracts;

namespace Sudoku.Controllers;

[ApiController]
[Route("api/datasets")]
public sealed class DatasetsController : ControllerBase
{
    private readonly ISender _sender;
    private readonly ILogger<DatasetsController> _logger;

    public DatasetsController(
        ISender sender,
        ILogger<DatasetsController> logger)
    {
        _sender = sender;
        _logger = logger;
    }

    [Authorize]
    [HttpGet("raw-candidates")]
    [ProducesResponseType(typeof(IReadOnlyList<RawDatasetCandidateApiResponse>), StatusCodes.Status200OK)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status500InternalServerError)]
    public async Task<IActionResult> ListRawCandidatesAsync(CancellationToken cancellationToken)
    {
        try
        {
            var result = await _sender.Send(new ListRawDatasetCandidatesQuery(), cancellationToken);
            var response = result.Items
                .Select(item => new RawDatasetCandidateApiResponse(
                    Name: item.Name,
                    Type: item.Type))
                .ToArray();

            return Ok(response);
        }
        catch (Exception exception) when (exception is IOException or UnauthorizedAccessException)
        {
            return StatusCode(
                StatusCodes.Status500InternalServerError,
                new ErrorApiResponse(
                    ErrorType: ListRawDatasetCandidatesErrorTypes.ScanFailed,
                    Message: "Nie udało się odczytać kandydatów datasetów z katalogu źródłowego."));
        }
    }

    [Authorize]
    [HttpGet("preparations")]
    [ProducesResponseType(typeof(DatasetPreparationsListApiResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status500InternalServerError)]
    public async Task<IActionResult> ListPreparationsAsync(CancellationToken cancellationToken)
    {
        try
        {
            var result = await _sender.Send(new ListDatasetPreparationsQuery(), cancellationToken);
            var items = result.Items
                .Select(ToDatasetPreparationListItemApiResponse)
                .ToArray();

            return Ok(new DatasetPreparationsListApiResponse(
                Items: items,
                TotalCount: result.TotalCount));
        }
        catch (Exception exception) when (exception is IOException
                                         or UnauthorizedAccessException
                                         or InvalidDataException
                                         or JsonException
                                         or FileStorageItemNotFoundException)
        {
            return StatusCode(
                StatusCodes.Status500InternalServerError,
                new ErrorApiResponse(
                    ErrorType: ListDatasetPreparationsErrorTypes.ReadFailed,
                    Message: "Nie udało się odczytać listy przygotowań datasetów."));
        }
    }

    [Authorize]
    [HttpGet("preparations/{preparationName}")]
    [ProducesResponseType(typeof(DatasetPreparationApiResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status400BadRequest)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status404NotFound)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status500InternalServerError)]
    public async Task<IActionResult> GetPreparationByNameAsync(
        [FromRoute] string? preparationName,
        CancellationToken cancellationToken)
    {
        _logger.LogInformation(
            "Rozpoczęto odczyt szczegółów przygotowania datasetu. PreparationName={PreparationName}.",
            preparationName);

        try
        {
            var result = await _sender.Send(
                new GetDatasetPreparationDetailsQuery(preparationName),
                cancellationToken);
            var response = ToDatasetPreparationApiResponse(result);

            _logger.LogInformation(
                "Zakończono odczyt szczegółów przygotowania datasetu. PreparationName={PreparationName}, Status={Status}.",
                response.PreparationName,
                response.Status);

            return Ok(response);
        }
        catch (ValidationException exception)
        {
            return MapDatasetPreparationDetailsValidationError(exception);
        }
        catch (DatasetPreparationNotFoundException exception)
        {
            _logger.LogWarning(
                exception,
                "Nie znaleziono przygotowania datasetu. PreparationName={PreparationName}, ErrorType={ErrorType}.",
                preparationName,
                GetDatasetPreparationDetailsErrorTypes.DatasetPreparationNotFound);

            return NotFound(new ErrorApiResponse(
                ErrorType: GetDatasetPreparationDetailsErrorTypes.DatasetPreparationNotFound,
                Message: exception.Message));
        }
        catch (Exception exception) when (exception is IOException
                                         or UnauthorizedAccessException
                                         or InvalidDataException
                                         or JsonException)
        {
            _logger.LogError(
                exception,
                "Nie udało się odczytać szczegółów przygotowania datasetu. PreparationName={PreparationName}, ErrorType={ErrorType}.",
                preparationName,
                GetDatasetPreparationDetailsErrorTypes.DatasetPreparationReadFailed);

            return StatusCode(
                StatusCodes.Status500InternalServerError,
                new ErrorApiResponse(
                    ErrorType: GetDatasetPreparationDetailsErrorTypes.DatasetPreparationReadFailed,
                    Message: "Nie udało się odczytać szczegółów przygotowania datasetu."));
        }
    }

    [Authorize]
    [HttpGet("preparations/{preparationName}/board/folders")]
    [ProducesResponseType(typeof(DatasetPreparationFoldersApiResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status400BadRequest)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status404NotFound)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status409Conflict)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status500InternalServerError)]
    public async Task<IActionResult> GetPreparationBoardFoldersAsync(
        [FromRoute] string? preparationName,
        CancellationToken cancellationToken)
    {
        const string type = "board";

        _logger.LogInformation(
            "Rozpoczęto odczyt listy folderów preparation. PreparationName={PreparationName}, Type={Type}.",
            preparationName,
            type);

        try
        {
            var result = await _sender.Send(
                new GetDatasetPreparationFoldersQuery(preparationName, type),
                cancellationToken);
            var response = ToDatasetPreparationFoldersApiResponse(result);

            _logger.LogInformation(
                "Zakończono odczyt listy folderów preparation. PreparationName={PreparationName}, Type={Type}, TotalCount={TotalCount}.",
                response.PreparationName,
                response.Type,
                response.TotalCount);

            return Ok(response);
        }
        catch (ValidationException exception)
        {
            return MapDatasetPreparationFoldersValidationError(exception);
        }
        catch (DatasetPreparationNotFoundException exception)
        {
            _logger.LogWarning(
                exception,
                "Nie znaleziono przygotowania datasetu dla odczytu folderów. PreparationName={PreparationName}, Type={Type}, ErrorType={ErrorType}.",
                preparationName,
                type,
                GetDatasetPreparationFoldersErrorTypes.DatasetPreparationNotFound);

            return NotFound(new ErrorApiResponse(
                ErrorType: GetDatasetPreparationFoldersErrorTypes.DatasetPreparationNotFound,
                Message: exception.Message));
        }
        catch (DatasetPreparationArtifactsNotReadyException exception)
        {
            _logger.LogWarning(
                exception,
                "Przygotowanie datasetu nie jest gotowe do odczytu folderów. PreparationName={PreparationName}, Type={Type}, Status={Status}, ErrorType={ErrorType}.",
                exception.PreparationName,
                type,
                exception.Status,
                GetDatasetPreparationFoldersErrorTypes.DatasetPreparationArtifactsNotReady);

            return Conflict(new ErrorApiResponse(
                ErrorType: GetDatasetPreparationFoldersErrorTypes.DatasetPreparationArtifactsNotReady,
                Message: exception.Message));
        }
        catch (Exception exception) when (exception is IOException
                                         or UnauthorizedAccessException
                                         or InvalidDataException
                                         or JsonException
                                         or FileStorageItemNotFoundException)
        {
            _logger.LogError(
                exception,
                "Nie udało się odczytać listy folderów preparation. PreparationName={PreparationName}, Type={Type}, ErrorType={ErrorType}.",
                preparationName,
                type,
                GetDatasetPreparationFoldersErrorTypes.DatasetPreparationFoldersReadFailed);

            return StatusCode(
                StatusCodes.Status500InternalServerError,
                new ErrorApiResponse(
                    ErrorType: GetDatasetPreparationFoldersErrorTypes.DatasetPreparationFoldersReadFailed,
                    Message: "Nie udało się odczytać listy folderów preparation."));
        }
    }

    [Authorize]
    [HttpGet("preparations/{preparationName}/digit/folders")]
    [ProducesResponseType(typeof(DatasetPreparationFoldersApiResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status400BadRequest)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status404NotFound)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status409Conflict)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status500InternalServerError)]
    public async Task<IActionResult> GetPreparationDigitFoldersAsync(
        [FromRoute] string? preparationName,
        CancellationToken cancellationToken)
    {
        const string type = "digit";

        _logger.LogInformation(
            "Rozpoczęto odczyt listy folderów preparation. PreparationName={PreparationName}, Type={Type}.",
            preparationName,
            type);

        try
        {
            var result = await _sender.Send(
                new GetDatasetPreparationFoldersQuery(preparationName, type),
                cancellationToken);
            var response = ToDatasetPreparationFoldersApiResponse(result);

            _logger.LogInformation(
                "Zakończono odczyt listy folderów preparation. PreparationName={PreparationName}, Type={Type}, TotalCount={TotalCount}.",
                response.PreparationName,
                response.Type,
                response.TotalCount);

            return Ok(response);
        }
        catch (ValidationException exception)
        {
            return MapDatasetPreparationFoldersValidationError(exception);
        }
        catch (DatasetPreparationNotFoundException exception)
        {
            _logger.LogWarning(
                exception,
                "Nie znaleziono przygotowania datasetu dla odczytu folderów. PreparationName={PreparationName}, Type={Type}, ErrorType={ErrorType}.",
                preparationName,
                type,
                GetDatasetPreparationFoldersErrorTypes.DatasetPreparationNotFound);

            return NotFound(new ErrorApiResponse(
                ErrorType: GetDatasetPreparationFoldersErrorTypes.DatasetPreparationNotFound,
                Message: exception.Message));
        }
        catch (DatasetPreparationArtifactsNotReadyException exception)
        {
            _logger.LogWarning(
                exception,
                "Przygotowanie datasetu nie jest gotowe do odczytu folderów. PreparationName={PreparationName}, Type={Type}, Status={Status}, ErrorType={ErrorType}.",
                exception.PreparationName,
                type,
                exception.Status,
                GetDatasetPreparationFoldersErrorTypes.DatasetPreparationArtifactsNotReady);

            return Conflict(new ErrorApiResponse(
                ErrorType: GetDatasetPreparationFoldersErrorTypes.DatasetPreparationArtifactsNotReady,
                Message: exception.Message));
        }
        catch (Exception exception) when (exception is IOException
                                         or UnauthorizedAccessException
                                         or InvalidDataException
                                         or JsonException
                                         or FileStorageItemNotFoundException)
        {
            _logger.LogError(
                exception,
                "Nie udało się odczytać listy folderów preparation. PreparationName={PreparationName}, Type={Type}, ErrorType={ErrorType}.",
                preparationName,
                type,
                GetDatasetPreparationFoldersErrorTypes.DatasetPreparationFoldersReadFailed);

            return StatusCode(
                StatusCodes.Status500InternalServerError,
                new ErrorApiResponse(
                    ErrorType: GetDatasetPreparationFoldersErrorTypes.DatasetPreparationFoldersReadFailed,
                    Message: "Nie udało się odczytać listy folderów preparation."));
        }
    }

    [Authorize]
    [HttpGet("preparations/{preparationName}/board/{sourceName}/files")]
    [ProducesResponseType(typeof(DatasetPreparationBoardFilesApiResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status400BadRequest)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status404NotFound)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status409Conflict)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status500InternalServerError)]
    public async Task<IActionResult> GetPreparationBoardFilesAsync(
        [FromRoute] string? preparationName,
        [FromRoute] string? sourceName,
        [FromQuery] int? page,
        [FromQuery] int? pageSize,
        CancellationToken cancellationToken)
    {
        _logger.LogInformation(
            "Rozpoczęto odczyt listy plansz preparation. PreparationName={PreparationName}, SourceName={SourceName}, Page={Page}, PageSize={PageSize}.",
            preparationName,
            sourceName,
            page,
            pageSize);

        try
        {
            var result = await _sender.Send(
                new GetDatasetPreparationBoardFilesQuery(preparationName, sourceName, page, pageSize),
                cancellationToken);
            var response = ToDatasetPreparationBoardFilesApiResponse(result);

            _logger.LogInformation(
                "Zakończono odczyt listy plansz preparation. PreparationName={PreparationName}, SourceName={SourceName}, Page={Page}, PageSize={PageSize}, TotalCount={TotalCount}, ReturnedItemsCount={ReturnedItemsCount}.",
                response.PreparationName,
                response.SourceName,
                response.Page,
                response.PageSize,
                response.TotalCount,
                response.Items.Count);

            return Ok(response);
        }
        catch (ValidationException exception)
        {
            return MapDatasetPreparationBoardFilesValidationError(exception);
        }
        catch (DatasetPreparationNotFoundException exception)
        {
            _logger.LogWarning(
                exception,
                "Nie znaleziono przygotowania datasetu dla odczytu listy plansz. PreparationName={PreparationName}, SourceName={SourceName}, ErrorType={ErrorType}.",
                preparationName,
                sourceName,
                GetDatasetPreparationBoardFilesErrorTypes.DatasetPreparationNotFound);

            return NotFound(new ErrorApiResponse(
                ErrorType: GetDatasetPreparationBoardFilesErrorTypes.DatasetPreparationNotFound,
                Message: exception.Message));
        }
        catch (DatasetPreparationSourceNotFoundException exception)
        {
            _logger.LogWarning(
                exception,
                "Nie znaleziono źródła board dla odczytu listy plansz. PreparationName={PreparationName}, SourceName={SourceName}, ErrorType={ErrorType}.",
                exception.PreparationName,
                exception.SourceName,
                GetDatasetPreparationBoardFilesErrorTypes.DatasetPreparationSourceNotFound);

            return NotFound(new ErrorApiResponse(
                ErrorType: GetDatasetPreparationBoardFilesErrorTypes.DatasetPreparationSourceNotFound,
                Message: exception.Message));
        }
        catch (DatasetPreparationArtifactsNotReadyException exception)
        {
            _logger.LogWarning(
                exception,
                "Przygotowanie datasetu nie jest gotowe do odczytu listy plansz. PreparationName={PreparationName}, SourceName={SourceName}, Status={Status}, ErrorType={ErrorType}.",
                exception.PreparationName,
                sourceName,
                exception.Status,
                GetDatasetPreparationBoardFilesErrorTypes.DatasetPreparationArtifactsNotReady);

            return Conflict(new ErrorApiResponse(
                ErrorType: GetDatasetPreparationBoardFilesErrorTypes.DatasetPreparationArtifactsNotReady,
                Message: exception.Message));
        }
        catch (Exception exception) when (exception is IOException
                                         or UnauthorizedAccessException
                                         or InvalidDataException
                                         or JsonException
                                         or FileStorageItemNotFoundException)
        {
            _logger.LogError(
                exception,
                "Nie udało się odczytać listy plansz preparation. PreparationName={PreparationName}, SourceName={SourceName}, ErrorType={ErrorType}.",
                preparationName,
                sourceName,
                GetDatasetPreparationBoardFilesErrorTypes.DatasetPreparationBoardFilesReadFailed);

            return StatusCode(
                StatusCodes.Status500InternalServerError,
                new ErrorApiResponse(
                    ErrorType: GetDatasetPreparationBoardFilesErrorTypes.DatasetPreparationBoardFilesReadFailed,
                    Message: "Nie udało się odczytać listy plansz preparation."));
        }
    }

    [Authorize]
    [HttpGet("preparations/{preparationName}/board/{sourceName}/files/{boardFolderName}/image")]
    [ProducesResponseType(typeof(ImageApiResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status400BadRequest)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status404NotFound)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status409Conflict)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status500InternalServerError)]
    public async Task<IActionResult> GetPreparationBoardImageAsync(
        [FromRoute] string? preparationName,
        [FromRoute] string? sourceName,
        [FromRoute] string? boardFolderName,
        CancellationToken cancellationToken)
    {
        _logger.LogInformation(
            "Rozpoczęto odczyt obrazu planszy preparation. PreparationName={PreparationName}, SourceName={SourceName}, BoardFolderName={BoardFolderName}.",
            preparationName,
            sourceName,
            boardFolderName);

        try
        {
            var result = await _sender.Send(
                new GetDatasetPreparationBoardImageQuery(preparationName, sourceName, boardFolderName),
                cancellationToken);
            var response = ToImageApiResponse(result);

            _logger.LogInformation(
                "Zakończono odczyt obrazu planszy preparation. PreparationName={PreparationName}, SourceName={SourceName}, BoardFolderName={BoardFolderName}, MimeType={MimeType}.",
                preparationName,
                sourceName,
                boardFolderName,
                response.MimeType);

            return Ok(response);
        }
        catch (ValidationException exception)
        {
            return MapDatasetPreparationBoardImageValidationError(exception);
        }
        catch (DatasetPreparationNotFoundException exception)
        {
            _logger.LogWarning(
                exception,
                "Nie znaleziono przygotowania datasetu dla odczytu obrazu planszy. PreparationName={PreparationName}, SourceName={SourceName}, BoardFolderName={BoardFolderName}, ErrorType={ErrorType}.",
                preparationName,
                sourceName,
                boardFolderName,
                GetDatasetPreparationBoardImageErrorTypes.DatasetPreparationNotFound);

            return NotFound(new ErrorApiResponse(
                ErrorType: GetDatasetPreparationBoardImageErrorTypes.DatasetPreparationNotFound,
                Message: exception.Message));
        }
        catch (DatasetPreparationSourceNotFoundException exception)
        {
            _logger.LogWarning(
                exception,
                "Nie znaleziono źródła board dla odczytu obrazu planszy. PreparationName={PreparationName}, SourceName={SourceName}, BoardFolderName={BoardFolderName}, ErrorType={ErrorType}.",
                exception.PreparationName,
                exception.SourceName,
                boardFolderName,
                GetDatasetPreparationBoardImageErrorTypes.DatasetPreparationSourceNotFound);

            return NotFound(new ErrorApiResponse(
                ErrorType: GetDatasetPreparationBoardImageErrorTypes.DatasetPreparationSourceNotFound,
                Message: exception.Message));
        }
        catch (DatasetPreparationBoardFileNotFoundException exception)
        {
            _logger.LogWarning(
                exception,
                "Nie znaleziono planszy dla odczytu obrazu preparation. PreparationName={PreparationName}, SourceName={SourceName}, BoardFolderName={BoardFolderName}, ErrorType={ErrorType}.",
                exception.PreparationName,
                exception.SourceName,
                exception.BoardFolderName,
                GetDatasetPreparationBoardImageErrorTypes.DatasetPreparationBoardFileNotFound);

            return NotFound(new ErrorApiResponse(
                ErrorType: GetDatasetPreparationBoardImageErrorTypes.DatasetPreparationBoardFileNotFound,
                Message: exception.Message));
        }
        catch (DatasetPreparationArtifactsNotReadyException exception)
        {
            _logger.LogWarning(
                exception,
                "Przygotowanie datasetu nie jest gotowe do odczytu obrazu planszy. PreparationName={PreparationName}, SourceName={SourceName}, BoardFolderName={BoardFolderName}, Status={Status}, ErrorType={ErrorType}.",
                exception.PreparationName,
                sourceName,
                boardFolderName,
                exception.Status,
                GetDatasetPreparationBoardImageErrorTypes.DatasetPreparationArtifactsNotReady);

            return Conflict(new ErrorApiResponse(
                ErrorType: GetDatasetPreparationBoardImageErrorTypes.DatasetPreparationArtifactsNotReady,
                Message: exception.Message));
        }
        catch (Exception exception) when (exception is IOException
                                         or UnauthorizedAccessException
                                         or InvalidDataException
                                         or JsonException
                                         or FileStorageItemNotFoundException)
        {
            _logger.LogError(
                exception,
                "Nie udało się odczytać obrazu planszy preparation. PreparationName={PreparationName}, SourceName={SourceName}, BoardFolderName={BoardFolderName}, ErrorType={ErrorType}.",
                preparationName,
                sourceName,
                boardFolderName,
                GetDatasetPreparationBoardImageErrorTypes.DatasetPreparationBoardImageReadFailed);

            return StatusCode(
                StatusCodes.Status500InternalServerError,
                new ErrorApiResponse(
                    ErrorType: GetDatasetPreparationBoardImageErrorTypes.DatasetPreparationBoardImageReadFailed,
                    Message: "Nie udało się odczytać obrazu planszy preparation."));
        }
    }

    [Authorize]
    [HttpDelete("preparations/{preparationName}/board/{sourceName}/files/{boardFolderName}")]
    [ProducesResponseType(typeof(DeleteDatasetPreparationBoardFileApiResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status400BadRequest)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status404NotFound)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status409Conflict)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status500InternalServerError)]
    public async Task<IActionResult> DeletePreparationBoardFileAsync(
        [FromRoute] string? preparationName,
        [FromRoute] string? sourceName,
        [FromRoute] string? boardFolderName,
        CancellationToken cancellationToken)
    {
        _logger.LogInformation(
            "Rozpoczęto usuwanie planszy preparation. PreparationName={PreparationName}, SourceName={SourceName}, BoardFolderName={BoardFolderName}.",
            preparationName,
            sourceName,
            boardFolderName);

        try
        {
            var result = await _sender.Send(
                new DeleteDatasetPreparationBoardFileCommand(preparationName, sourceName, boardFolderName),
                cancellationToken);
            var response = ToDeleteDatasetPreparationBoardFileApiResponse(result);

            _logger.LogInformation(
                "Zakończono usuwanie planszy preparation. PreparationName={PreparationName}, SourceName={SourceName}, BoardFolderName={BoardFolderName}, Deleted={Deleted}, RemainingItemsCount={RemainingItemsCount}.",
                response.PreparationName,
                response.SourceName,
                response.BoardFolderName,
                response.Deleted,
                response.RemainingItemsCount);

            return Ok(response);
        }
        catch (ValidationException exception)
        {
            return MapDeleteDatasetPreparationBoardFileValidationError(exception);
        }
        catch (DatasetPreparationNotFoundException exception)
        {
            _logger.LogWarning(
                exception,
                "Nie znaleziono przygotowania datasetu dla usunięcia planszy. PreparationName={PreparationName}, SourceName={SourceName}, BoardFolderName={BoardFolderName}, ErrorType={ErrorType}.",
                preparationName,
                sourceName,
                boardFolderName,
                DeleteDatasetPreparationBoardFileErrorTypes.DatasetPreparationNotFound);

            return NotFound(new ErrorApiResponse(
                ErrorType: DeleteDatasetPreparationBoardFileErrorTypes.DatasetPreparationNotFound,
                Message: exception.Message));
        }
        catch (DatasetPreparationSourceNotFoundException exception)
        {
            _logger.LogWarning(
                exception,
                "Nie znaleziono źródła board dla usunięcia planszy. PreparationName={PreparationName}, SourceName={SourceName}, BoardFolderName={BoardFolderName}, ErrorType={ErrorType}.",
                exception.PreparationName,
                exception.SourceName,
                boardFolderName,
                DeleteDatasetPreparationBoardFileErrorTypes.DatasetPreparationSourceNotFound);

            return NotFound(new ErrorApiResponse(
                ErrorType: DeleteDatasetPreparationBoardFileErrorTypes.DatasetPreparationSourceNotFound,
                Message: exception.Message));
        }
        catch (DatasetPreparationBoardFileNotFoundException exception)
        {
            _logger.LogWarning(
                exception,
                "Nie znaleziono planszy do usunięcia. PreparationName={PreparationName}, SourceName={SourceName}, BoardFolderName={BoardFolderName}, ErrorType={ErrorType}.",
                exception.PreparationName,
                exception.SourceName,
                exception.BoardFolderName,
                DeleteDatasetPreparationBoardFileErrorTypes.DatasetPreparationBoardFileNotFound);

            return NotFound(new ErrorApiResponse(
                ErrorType: DeleteDatasetPreparationBoardFileErrorTypes.DatasetPreparationBoardFileNotFound,
                Message: exception.Message));
        }
        catch (DatasetPreparationArtifactsNotReadyException exception)
        {
            _logger.LogWarning(
                exception,
                "Przygotowanie datasetu nie jest gotowe do usunięcia planszy. PreparationName={PreparationName}, SourceName={SourceName}, BoardFolderName={BoardFolderName}, Status={Status}, ErrorType={ErrorType}.",
                exception.PreparationName,
                sourceName,
                boardFolderName,
                exception.Status,
                DeleteDatasetPreparationBoardFileErrorTypes.DatasetPreparationArtifactsNotReady);

            return Conflict(new ErrorApiResponse(
                ErrorType: DeleteDatasetPreparationBoardFileErrorTypes.DatasetPreparationArtifactsNotReady,
                Message: exception.Message));
        }
        catch (Exception exception) when (exception is IOException
                                         or UnauthorizedAccessException
                                         or InvalidDataException
                                         or JsonException
                                         or FileStorageItemNotFoundException)
        {
            _logger.LogError(
                exception,
                "Nie udało się usunąć planszy preparation. PreparationName={PreparationName}, SourceName={SourceName}, BoardFolderName={BoardFolderName}, ErrorType={ErrorType}.",
                preparationName,
                sourceName,
                boardFolderName,
                DeleteDatasetPreparationBoardFileErrorTypes.DatasetPreparationBoardFileDeleteFailed);

            return StatusCode(
                StatusCodes.Status500InternalServerError,
                new ErrorApiResponse(
                    ErrorType: DeleteDatasetPreparationBoardFileErrorTypes.DatasetPreparationBoardFileDeleteFailed,
                    Message: "Nie udało się usunąć planszy preparation."));
        }
    }

    [Authorize]
    [HttpPost("preparations")]
    [ProducesResponseType(typeof(DatasetPreparationApiResponse), StatusCodes.Status202Accepted)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status400BadRequest)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status404NotFound)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status409Conflict)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status422UnprocessableEntity)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status500InternalServerError)]
    public async Task<IActionResult> CreatePreparationAsync(
        [FromBody] CreateDatasetPreparationApiEntry? entry,
        CancellationToken cancellationToken)
    {
        var command = new CreateDatasetPreparationCommand(
            PreparationName: entry?.PreparationName,
            Sources: entry?.Sources
                ?.Select(source => new CreateDatasetPreparationSourceDto(
                    Name: source.Name ?? string.Empty,
                    Type: source.Type ?? string.Empty))
                .ToArray());

        try
        {
            var result = await _sender.Send(command, cancellationToken);
            return StatusCode(StatusCodes.Status202Accepted, ToDatasetPreparationApiResponse(result));
        }
        catch (ValidationException exception)
        {
            return MapCreateDatasetPreparationValidationError(exception);
        }
        catch (RawDatasetNotFoundException exception)
        {
            return NotFound(new ErrorApiResponse(
                ErrorType: CreateDatasetPreparationErrorTypes.RawDatasetNotFound,
                Message: exception.Message));
        }
        catch (RawDatasetTypeMismatchException exception)
        {
            return UnprocessableEntity(new ErrorApiResponse(
                ErrorType: CreateDatasetPreparationErrorTypes.RawDatasetTypeMismatch,
                Message: exception.Message));
        }
        catch (FileStorageConflictException exception)
        {
            return Conflict(new ErrorApiResponse(
                ErrorType: CreateDatasetPreparationErrorTypes.PreparationNameConflict,
                Message: exception.Message));
        }
        catch (Exception)
        {
            return StatusCode(
                StatusCodes.Status500InternalServerError,
                new ErrorApiResponse(
                    ErrorType: CreateDatasetPreparationErrorTypes.PreparationStartFailed,
                    Message: "Nie udało się rozpocząć przygotowania datasetu."));
        }
    }

    [Authorize]
    [HttpPost("processed")]
    [ProducesResponseType(typeof(ProcessedDatasetApiResponse), StatusCodes.Status201Created)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status400BadRequest)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status404NotFound)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status409Conflict)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status422UnprocessableEntity)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status503ServiceUnavailable)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status504GatewayTimeout)]
    public async Task<IActionResult> CreateProcessedAsync(
        [FromBody] CreateProcessedDatasetApiEntry? entry,
        CancellationToken cancellationToken)
    {
        var command = new CreateProcessedDatasetCommand(
            Name: entry?.Name,
            Sources: entry?.Sources
                ?.Select(source => new SelectedRawDatasetSourceDto(
                    Name: source.Name,
                    Type: source.Type,
                    Splits: source.Splits))
                .ToArray());

        try
        {
            var result = await _sender.Send(command, cancellationToken);
            return StatusCode(StatusCodes.Status201Created, ToProcessedDatasetApiResponse(result));
        }
        catch (ValidationException exception)
        {
            return MapValidationError(exception);
        }
        catch (RawDatasetNotFoundException exception)
        {
            return NotFound(new ErrorApiResponse(
                ErrorType: CreateProcessedDatasetErrorTypes.RawDatasetNotFound,
                Message: exception.Message));
        }
        catch (RawDatasetTypeMismatchException exception)
        {
            return UnprocessableEntity(new ErrorApiResponse(
                ErrorType: CreateProcessedDatasetErrorTypes.RawDatasetTypeMismatch,
                Message: exception.Message));
        }
        catch (NoSamplesPreparedException exception)
        {
            return UnprocessableEntity(new ErrorApiResponse(
                ErrorType: CreateProcessedDatasetErrorTypes.NoSamplesPrepared,
                Message: exception.Message));
        }
        catch (FileStorageConflictException exception)
        {
            return Conflict(new ErrorApiResponse(
                ErrorType: CreateProcessedDatasetErrorTypes.ProcessedDatasetNameConflict,
                Message: exception.Message));
        }
        catch (FileStorageItemNotFoundException exception)
        {
            return StatusCode(
                StatusCodes.Status503ServiceUnavailable,
                new ErrorApiResponse(
                    ErrorType: CreateProcessedDatasetErrorTypes.ArtifactPromotionFailed,
                    Message: exception.Message));
        }
        catch (MlOperationFailedException exception)
        {
            return UnprocessableEntity(new ErrorApiResponse(
                ErrorType: exception.ErrorType,
                Message: exception.Message));
        }
        catch (MlServiceUnavailableException exception)
        {
            return StatusCode(
                StatusCodes.Status503ServiceUnavailable,
                new ErrorApiResponse(
                    ErrorType: CreateProcessedDatasetErrorTypes.MlUnavailable,
                    Message: exception.Message));
        }
        catch (MlServiceTimeoutException exception)
        {
            return StatusCode(
                StatusCodes.Status504GatewayTimeout,
                new ErrorApiResponse(
                    ErrorType: CreateProcessedDatasetErrorTypes.MlTimeout,
                    Message: exception.Message));
        }
    }

    [Authorize]
    [HttpGet("processed")]
    [ProducesResponseType(typeof(ProcessedDatasetsListApiResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status500InternalServerError)]
    public async Task<IActionResult> ListProcessedAsync(CancellationToken cancellationToken)
    {
        try
        {
            var result = await _sender.Send(new ListProcessedDatasetsQuery(), cancellationToken);
            var items = result.Items
                .Select(item => new ProcessedDatasetListItemApiResponse(
                    Name: item.Name,
                    FileName: item.FileName,
                    PreprocessingProfile: item.PreprocessingProfile,
                    CreatedAtUtc: item.CreatedAtUtc,
                    SampleCounts: new SplitSampleCountsApiResponse(
                        Train: item.SampleCounts.Train,
                        Val: item.SampleCounts.Val,
                        Test: item.SampleCounts.Test)))
                .ToArray();

            return Ok(new ProcessedDatasetsListApiResponse(
                Items: items,
                TotalCount: result.TotalCount));
        }
        catch (Exception exception) when (exception is IOException
                                         or UnauthorizedAccessException
                                         or InvalidDataException
                                         or JsonException
                                         or FileStorageItemNotFoundException)
        {
            return StatusCode(
                StatusCodes.Status500InternalServerError,
                new ErrorApiResponse(
                    ErrorType: ListProcessedDatasetsErrorTypes.ReadFailed,
                    Message: "Nie udało się odczytać listy przygotowanych datasetów."));
        }
    }

    private static ProcessedDatasetApiResponse ToProcessedDatasetApiResponse(
        CreateProcessedDatasetCommandResultDto result)
    {
        return new ProcessedDatasetApiResponse(
            Name: result.Name,
            FileName: result.FileName,
            PreprocessingProfile: result.PreprocessingProfile,
            CreatedAtUtc: result.CreatedAtUtc,
            Sources: result.Sources
                .Select(source => new SelectedRawDatasetSourceApiEntry(
                    Name: source.Name,
                    Type: source.Type,
                    Splits: source.Splits))
                .ToArray(),
            SampleCounts: new SplitSampleCountsApiResponse(
                Train: result.SampleCounts.Train,
                Val: result.SampleCounts.Val,
                Test: result.SampleCounts.Test),
            SourceReports: result.SourceReports
                .Select(report => new ProcessedDatasetSourceReportApiResponse(
                    Name: report.Name,
                    Type: report.Type,
                    ProcessedSampleCount: report.ProcessedSampleCount,
                    IncludedSampleCount: report.IncludedSampleCount,
                    EmptyCellCount: report.EmptyCellCount,
                    RejectedSampleCount: report.RejectedSampleCount,
                    Warnings: report.Warnings))
                .ToArray(),
            Warnings: result.Warnings);
    }

    private static DatasetPreparationApiResponse ToDatasetPreparationApiResponse(
        CreateDatasetPreparationCommandResultDto result)
    {
        return new DatasetPreparationApiResponse(
            PreparationName: result.PreparationName,
            CreatedAtUtc: result.CreatedAtUtc,
            Status: result.Status,
            Sources: result.Sources
                .Select(source => new DatasetPreparationSourceApiResponse(
                    Name: source.Name,
                    Type: source.Type,
                    PreparedItemsCount: source.PreparedItemsCount))
                .ToArray(),
            Warnings: result.Warnings);
    }

    private static DatasetPreparationApiResponse ToDatasetPreparationApiResponse(
        GetDatasetPreparationDetailsQueryResultDto result)
    {
        return new DatasetPreparationApiResponse(
            PreparationName: result.PreparationName,
            CreatedAtUtc: result.CreatedAtUtc,
            Status: result.Status,
            Sources: result.Sources
                .Select(source => new DatasetPreparationSourceApiResponse(
                    Name: source.Name,
                    Type: source.Type,
                    PreparedItemsCount: source.PreparedItemsCount))
                .ToArray(),
            Warnings: result.Warnings);
    }

    private static DatasetPreparationFoldersApiResponse ToDatasetPreparationFoldersApiResponse(
        GetDatasetPreparationFoldersQueryResultDto result)
    {
        return new DatasetPreparationFoldersApiResponse(
            PreparationName: result.PreparationName,
            Type: result.Type,
            Items: result.Items,
            TotalCount: result.TotalCount);
    }

    private static DatasetPreparationBoardFilesApiResponse ToDatasetPreparationBoardFilesApiResponse(
        GetDatasetPreparationBoardFilesQueryResultDto result)
    {
        return new DatasetPreparationBoardFilesApiResponse(
            PreparationName: result.PreparationName,
            SourceName: result.SourceName,
            Items: result.Items
                .Select(item => new DatasetPreparationBoardFileListItemApiResponse(
                    BoardFolderName: item.BoardFolderName,
                    ImageEndpoint: BuildDatasetPreparationBoardImageEndpoint(
                        result.PreparationName,
                        result.SourceName,
                        item.BoardFolderName)))
                .ToArray(),
            Page: result.Page,
            PageSize: result.PageSize,
            TotalCount: result.TotalCount);
    }

    private static DatasetPreparationListItemApiResponse ToDatasetPreparationListItemApiResponse(
        DatasetPreparationListItemDto item)
    {
        return new DatasetPreparationListItemApiResponse(
            PreparationName: item.PreparationName,
            CreatedAtUtc: item.CreatedAtUtc,
            Status: item.Status,
            BoardSourcesCount: item.BoardSourcesCount,
            DigitSourcesCount: item.DigitSourcesCount);
    }

    private static ImageApiResponse ToImageApiResponse(GetDatasetPreparationBoardImageQueryResultDto result)
    {
        return new ImageApiResponse(
            MimeType: result.MimeType,
            Base64: result.Base64);
    }

    private static DeleteDatasetPreparationBoardFileApiResponse ToDeleteDatasetPreparationBoardFileApiResponse(
        DeleteDatasetPreparationBoardFileCommandResultDto result)
    {
        return new DeleteDatasetPreparationBoardFileApiResponse(
            PreparationName: result.PreparationName,
            SourceName: result.SourceName,
            BoardFolderName: result.BoardFolderName,
            Deleted: result.Deleted,
            RemainingItemsCount: result.RemainingItemsCount);
    }

    private static IActionResult MapValidationError(ValidationException exception)
    {
        var failure = exception.Errors.FirstOrDefault();
        var errorType = failure?.ErrorCode ?? CreateProcessedDatasetErrorTypes.InvalidRequest;
        var message = failure?.ErrorMessage ?? "Nieprawidłowe dane wejściowe.";
        var statusCode = errorType switch
        {
            CreateProcessedDatasetErrorTypes.InvalidDatasetSplitSelection => StatusCodes.Status400BadRequest,
            _ => StatusCodes.Status400BadRequest
        };

        return new ObjectResult(new ErrorApiResponse(
            ErrorType: errorType,
            Message: message))
        {
            StatusCode = statusCode
        };
    }

    private static IActionResult MapCreateDatasetPreparationValidationError(ValidationException exception)
    {
        var failure = exception.Errors.FirstOrDefault();
        var errorType = failure?.ErrorCode ?? CreateDatasetPreparationErrorTypes.InvalidRequest;
        var message = failure?.ErrorMessage ?? "Nieprawidłowe dane wejściowe.";

        return new ObjectResult(new ErrorApiResponse(
            ErrorType: errorType,
            Message: message))
        {
            StatusCode = StatusCodes.Status400BadRequest
        };
    }

    private static IActionResult MapDatasetPreparationDetailsValidationError(ValidationException exception)
    {
        var failure = exception.Errors.FirstOrDefault();
        var errorType = failure?.ErrorCode ?? GetDatasetPreparationDetailsErrorTypes.InvalidDatasetPreparationName;
        var message = failure?.ErrorMessage ?? "Nieprawidłowa nazwa przygotowania datasetu.";

        return new ObjectResult(new ErrorApiResponse(
            ErrorType: errorType,
            Message: message))
        {
            StatusCode = StatusCodes.Status400BadRequest
        };
    }

    private static IActionResult MapDatasetPreparationFoldersValidationError(ValidationException exception)
    {
        var failure = exception.Errors.FirstOrDefault();
        var errorType = failure?.ErrorCode ?? GetDatasetPreparationFoldersErrorTypes.InvalidDatasetPreparationName;
        var message = failure?.ErrorMessage ?? "Nieprawidłowe parametry odczytu folderów preparation.";

        return new ObjectResult(new ErrorApiResponse(
            ErrorType: errorType,
            Message: message))
        {
            StatusCode = StatusCodes.Status400BadRequest
        };
    }

    private static IActionResult MapDatasetPreparationBoardFilesValidationError(ValidationException exception)
    {
        var failure = exception.Errors.FirstOrDefault();
        var errorType = failure?.ErrorCode ?? GetDatasetPreparationBoardFilesErrorTypes.InvalidDatasetPreparationName;
        var message = failure?.ErrorMessage ?? "Nieprawidłowe parametry odczytu listy plansz preparation.";

        return new ObjectResult(new ErrorApiResponse(
            ErrorType: errorType,
            Message: message))
        {
            StatusCode = StatusCodes.Status400BadRequest
        };
    }

    private static IActionResult MapDatasetPreparationBoardImageValidationError(ValidationException exception)
    {
        var failure = exception.Errors.FirstOrDefault();
        var errorType = failure?.ErrorCode ?? GetDatasetPreparationBoardImageErrorTypes.InvalidDatasetPreparationName;
        var message = failure?.ErrorMessage ?? "Nieprawidłowe parametry odczytu obrazu planszy preparation.";

        return new ObjectResult(new ErrorApiResponse(
            ErrorType: errorType,
            Message: message))
        {
            StatusCode = StatusCodes.Status400BadRequest
        };
    }

    private static IActionResult MapDeleteDatasetPreparationBoardFileValidationError(ValidationException exception)
    {
        var failure = exception.Errors.FirstOrDefault();
        var errorType = failure?.ErrorCode ?? DeleteDatasetPreparationBoardFileErrorTypes.InvalidDatasetPreparationName;
        var message = failure?.ErrorMessage ?? "Nieprawidłowe parametry usuwania planszy preparation.";

        return new ObjectResult(new ErrorApiResponse(
            ErrorType: errorType,
            Message: message))
        {
            StatusCode = StatusCodes.Status400BadRequest
        };
    }

    private static string BuildDatasetPreparationBoardImageEndpoint(
        string preparationName,
        string sourceName,
        string boardFolderName)
    {
        return $"/api/datasets/preparations/{Uri.EscapeDataString(preparationName)}/board/{Uri.EscapeDataString(sourceName)}/files/{Uri.EscapeDataString(boardFolderName)}/image";
    }
}
