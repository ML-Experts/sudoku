using MediatR;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using System.Text.Json;
using Sudoku.Application.Storage;
using Sudoku.Application.Trainings;
using Sudoku.Contracts;

namespace Sudoku.Controllers;

[ApiController]
[Route("api/trainings")]
public sealed class TrainingsController : ControllerBase
{
    private readonly ISender _sender;

    public TrainingsController(ISender sender)
    {
        _sender = sender;
    }

    [Authorize]
    [HttpGet("active")]
    [ProducesResponseType(typeof(TrainingRunApiResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status204NoContent)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status500InternalServerError)]
    public async Task<IActionResult> GetActiveAsync(CancellationToken cancellationToken)
    {
        try
        {
            var result = await _sender.Send(new GetActiveTrainingRunQuery(), cancellationToken);
            if (!result.HasActiveRun || result.Run is null)
            {
                return NoContent();
            }

            return Ok(new TrainingRunApiResponse(
                RunName: result.Run.RunName,
                Status: result.Run.Status,
                CreatedAtUtc: result.Run.CreatedAtUtc,
                BaseModelName: result.Run.BaseModelName,
                ProducedModelName: result.Run.ProducedModelName,
                ProcessedDatasetName: result.Run.ProcessedDatasetName,
                TrainingMode: result.Run.TrainingMode,
                TrainingProfileName: result.Run.TrainingProfileName,
                AugmentationProfileName: result.Run.AugmentationProfileName,
                BenchmarkName: result.Run.BenchmarkName,
                Seed: result.Run.Seed,
                ProgressChannelUrl: result.Run.ProgressChannelUrl));
        }
        catch (InvalidOperationException)
        {
            return StatusCode(
                StatusCodes.Status500InternalServerError,
                new ErrorApiResponse(
                    ErrorType: GetActiveTrainingRunErrorTypes.InvariantViolation,
                    Message: "Wykryto niespójny stan aktywnych runów treningowych."));
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
                    ErrorType: GetActiveTrainingRunErrorTypes.ReadFailed,
                    Message: "Nie udało się odczytać aktywnego runu treningowego."));
        }
    }
}
