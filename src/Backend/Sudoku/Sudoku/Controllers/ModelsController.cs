using MediatR;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using System.Text.Json;
using Sudoku.Application.ModelsRegistry;
using Sudoku.Application.Storage;
using Sudoku.Contracts;

namespace Sudoku.Controllers;

[ApiController]
[Route("api/models")]
public sealed class ModelsController : ControllerBase
{
    private readonly ISender _sender;

    public ModelsController(ISender sender)
    {
        _sender = sender;
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
}
