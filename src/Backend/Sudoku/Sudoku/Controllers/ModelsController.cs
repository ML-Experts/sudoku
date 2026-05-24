using MediatR;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using System.Text.Json;
using FluentValidation;
using Sudoku.Application.ModelsActive;
using Sudoku.Application.ModelsRegistry;
using Sudoku.Application.Storage;
using Sudoku.Contracts;

namespace Sudoku.Controllers;

[ApiController]
[Route("api/models")]
public sealed class ModelsController : ControllerBase
{
    private readonly ISender _sender;
    private readonly ILogger<ModelsController> _logger;

    public ModelsController(
        ISender sender,
        ILogger<ModelsController> logger)
    {
        _sender = sender;
        _logger = logger;
    }

    [Authorize]
    [HttpGet("active")]
    [ProducesResponseType(typeof(ActiveModelApiResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status204NoContent)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status409Conflict)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status500InternalServerError)]
    public async Task<IActionResult> GetActiveAsync(CancellationToken cancellationToken)
    {
        _logger.LogInformation("Rozpoczęto odczyt aktywnego modelu.");

        try
        {
            var result = await _sender.Send(new GetActiveModelQuery(), cancellationToken);
            if (result.ActiveModel is null)
            {
                return NoContent();
            }

            _logger.LogInformation(
                "Zwrócono aktywny model. ModelName={ModelName}.",
                result.ActiveModel.ModelName);

            return Ok(MapActiveModel(result.ActiveModel));
        }
        catch (ActiveModelPointerInvalidException exception)
        {
            _logger.LogWarning(
                exception,
                "Wskaźnik aktywnego modelu jest niespójny. ErrorType={ErrorType}. ModelName={ModelName}.",
                GetActiveModelErrorTypes.PointerInvalid,
                exception.ModelName);

            return Conflict(new ErrorApiResponse(
                ErrorType: GetActiveModelErrorTypes.PointerInvalid,
                Message: exception.Message));
        }
        catch (ActiveModelNotFoundException exception)
        {
            _logger.LogWarning(
                exception,
                "Wskaźnik aktywnego modelu wskazuje brakujący model. ErrorType={ErrorType}. ModelName={ModelName}.",
                GetActiveModelErrorTypes.PointerInvalid,
                exception.ModelName);

            return Conflict(new ErrorApiResponse(
                ErrorType: GetActiveModelErrorTypes.PointerInvalid,
                Message: exception.Message));
        }
        catch (ActiveModelCannotUseForInferenceException exception)
        {
            _logger.LogWarning(
                exception,
                "Aktywny model utracił capability inferencji. ErrorType={ErrorType}. ModelName={ModelName}.",
                GetActiveModelErrorTypes.CannotUseForInference,
                exception.ModelName);

            return Conflict(new ErrorApiResponse(
                ErrorType: GetActiveModelErrorTypes.CannotUseForInference,
                Message: exception.Message));
        }
        catch (ActiveModelManifestInvalidException exception)
        {
            _logger.LogWarning(
                exception,
                "Manifest aktywnego modelu jest nieaktywowalny. ErrorType={ErrorType}. ModelName={ModelName}.",
                GetActiveModelErrorTypes.ManifestInvalid,
                exception.ModelName);

            return Conflict(new ErrorApiResponse(
                ErrorType: GetActiveModelErrorTypes.ManifestInvalid,
                Message: exception.Message));
        }
        catch (ActiveModelPointerReadException exception)
        {
            _logger.LogError(
                exception,
                "Nie udało się odczytać wskaźnika aktywnego modelu. ErrorType={ErrorType}.",
                GetActiveModelErrorTypes.ReadFailed);

            return StatusCode(
                StatusCodes.Status500InternalServerError,
                new ErrorApiResponse(
                    ErrorType: GetActiveModelErrorTypes.ReadFailed,
                    Message: "Nie udało się odczytać wskaźnika aktywnego modelu."));
        }
    }

    [Authorize]
    [HttpPut("active")]
    [ProducesResponseType(typeof(ActiveModelApiResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status400BadRequest)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status404NotFound)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status409Conflict)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status422UnprocessableEntity)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status500InternalServerError)]
    public async Task<IActionResult> SetActiveAsync(
        [FromBody] SetActiveModelApiEntry? entry,
        CancellationToken cancellationToken)
    {
        var command = new SetActiveModelCommand(entry?.ModelName);
        _logger.LogInformation("Rozpoczęto ustawianie aktywnego modelu. ModelName={ModelName}.", command.ModelName);

        try
        {
            var result = await _sender.Send(command, cancellationToken);
            _logger.LogInformation("Zapisano aktywny wskaźnik modelu. ModelName={ModelName}.", result.ModelName);

            return Ok(MapActiveModel(result));
        }
        catch (ValidationException exception)
        {
            return MapValidationError(exception);
        }
        catch (ActiveModelNotFoundException exception)
        {
            _logger.LogWarning(
                exception,
                "Odrzucono ustawienie aktywnego modelu. ErrorType={ErrorType}. ModelName={ModelName}.",
                SetActiveModelErrorTypes.NotFound,
                exception.ModelName);

            return NotFound(new ErrorApiResponse(
                ErrorType: SetActiveModelErrorTypes.NotFound,
                Message: exception.Message));
        }
        catch (ActiveModelCannotUseForInferenceException exception)
        {
            _logger.LogWarning(
                exception,
                "Odrzucono model bez capability inferencji. ErrorType={ErrorType}. ModelName={ModelName}.",
                SetActiveModelErrorTypes.CannotUseForInference,
                exception.ModelName);

            return Conflict(new ErrorApiResponse(
                ErrorType: SetActiveModelErrorTypes.CannotUseForInference,
                Message: exception.Message));
        }
        catch (ActiveModelManifestInvalidException exception)
        {
            _logger.LogWarning(
                exception,
                "Odrzucono model z nieaktywowalnym manifestem. ErrorType={ErrorType}. ModelName={ModelName}.",
                SetActiveModelErrorTypes.ManifestInvalid,
                exception.ModelName);

            return UnprocessableEntity(new ErrorApiResponse(
                ErrorType: SetActiveModelErrorTypes.ManifestInvalid,
                Message: exception.Message));
        }
        catch (ActiveModelPointerWriteException exception)
        {
            _logger.LogError(
                exception,
                "Nie udało się zapisać wskaźnika aktywnego modelu. ErrorType={ErrorType}. ModelName={ModelName}.",
                SetActiveModelErrorTypes.PointerWriteFailed,
                exception.ModelName);

            return StatusCode(
                StatusCodes.Status500InternalServerError,
                new ErrorApiResponse(
                    ErrorType: SetActiveModelErrorTypes.PointerWriteFailed,
                    Message: "Nie udało się zapisać wskaźnika aktywnego modelu."));
        }
        catch (Exception exception) when (exception is IOException
                                         or UnauthorizedAccessException
                                         or InvalidOperationException
                                         or JsonException
                                         or FileStorageItemNotFoundException)
        {
            _logger.LogError(
                exception,
                "Nie udało się ustawić aktywnego modelu. ErrorType={ErrorType}.",
                SetActiveModelErrorTypes.PointerWriteFailed);

            return StatusCode(
                StatusCodes.Status500InternalServerError,
                new ErrorApiResponse(
                    ErrorType: SetActiveModelErrorTypes.PointerWriteFailed,
                    Message: "Nie udało się ustawić aktywnego modelu."));
        }
    }

    [Authorize]
    [HttpGet("registry")]
    [ProducesResponseType(typeof(RegistryModelsListApiResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status500InternalServerError)]
    public async Task<IActionResult> ListRegistryAsync(CancellationToken cancellationToken)
    {
        try
        {
            var result = await _sender.Send(new ListRegistryModelsQuery(), cancellationToken);
            var items = result.Items
                .Select(item => new RegistryModelListItemApiResponse(
                    Name: item.Name,
                    DisplayName: item.DisplayName,
                    SourceType: item.SourceType,
                    SourceRunName: item.SourceRunName,
                    ParentModelName: item.ParentModelName,
                    TrainingMode: item.TrainingMode,
                    InputProfile: item.InputProfile,
                    TrainingProfileName: item.TrainingProfileName,
                    AugmentationProfileName: item.AugmentationProfileName,
                    CreatedAtUtc: item.CreatedAtUtc,
                    CanStartTraining: item.CanStartTraining,
                    CanUseForInference: item.CanUseForInference,
                    Warnings: item.Warnings))
                .ToArray();

            return Ok(new RegistryModelsListApiResponse(
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
                    ErrorType: ListRegistryModelsErrorTypes.ReadFailed,
                    Message: "Nie udało się odczytać listy modeli z rejestru."));
        }
    }

    private static IActionResult MapValidationError(ValidationException exception)
    {
        var failure = exception.Errors.FirstOrDefault();
        var errorType = failure?.ErrorCode ?? SetActiveModelErrorTypes.InvalidRequest;
        var message = failure?.ErrorMessage ?? "Nieprawidłowe dane wejściowe.";

        return new ObjectResult(new ErrorApiResponse(
            ErrorType: errorType,
            Message: message))
        {
            StatusCode = StatusCodes.Status400BadRequest
        };
    }

    private static ActiveModelApiResponse MapActiveModel(SetActiveModelCommandResultDto model)
    {
        return new ActiveModelApiResponse(
            ModelName: model.ModelName,
            DisplayName: model.DisplayName,
            SourceType: model.SourceType,
            SourceRunName: model.SourceRunName,
            ParentModelName: model.ParentModelName,
            InputProfile: model.InputProfile,
            CanUseForInference: model.CanUseForInference,
            ActivatedAtUtc: model.ActivatedAtUtc);
    }

    private static ActiveModelApiResponse MapActiveModel(ActiveModelDto model)
    {
        return new ActiveModelApiResponse(
            ModelName: model.ModelName,
            DisplayName: model.DisplayName,
            SourceType: model.SourceType,
            SourceRunName: model.SourceRunName,
            ParentModelName: model.ParentModelName,
            InputProfile: model.InputProfile,
            CanUseForInference: model.CanUseForInference,
            ActivatedAtUtc: model.ActivatedAtUtc);
    }
}
