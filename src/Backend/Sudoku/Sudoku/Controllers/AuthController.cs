using FluentValidation;
using MediatR;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Sudoku.Application.Auth;
using Sudoku.Contracts;

namespace Sudoku.Controllers;

[ApiController]
[Route("api/auth")]
public sealed class AuthController : ControllerBase
{
    private readonly ISender _sender;

    public AuthController(ISender sender)
    {
        _sender = sender;
    }

    [AllowAnonymous]
    [HttpPost("login")]
    [ProducesResponseType(typeof(AuthTokenApiResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status400BadRequest)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status401Unauthorized)]
    public async Task<IActionResult> LoginAsync(
        [FromBody] AdminLoginApiEntry? entry,
        CancellationToken cancellationToken)
    {
        var command = new LoginCommand(entry?.Password);

        try
        {
            var result = await _sender.Send(command, cancellationToken);
            var response = new AuthTokenApiResponse(
                AccessToken: result.AccessToken,
                TokenType: result.TokenType,
                ExpiresAtUtc: result.ExpiresAtUtc.UtcDateTime.ToString("O"));

            return Ok(response);
        }
        catch (ValidationException exception)
        {
            return MapValidationError(exception);
        }
        catch (InvalidAdminCredentialsException exception)
        {
            return Unauthorized(new ErrorApiResponse(
                ErrorType: AdminAuthErrorTypes.InvalidCredentials,
                Message: exception.Message));
        }
    }

    private static IActionResult MapValidationError(ValidationException exception)
    {
        var failure = exception.Errors.FirstOrDefault();
        var errorType = failure?.ErrorCode ?? AdminAuthErrorTypes.InvalidRequest;
        var message = failure?.ErrorMessage ?? "Nieprawidłowe dane wejściowe.";

        return new BadRequestObjectResult(new ErrorApiResponse(
            ErrorType: errorType,
            Message: message));
    }
}
