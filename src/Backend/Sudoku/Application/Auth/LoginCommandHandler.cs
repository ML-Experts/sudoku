using System.Security.Cryptography;
using System.Text;
using MediatR;
using Microsoft.Extensions.Options;

namespace Sudoku.Application.Auth;

public sealed class LoginCommandHandler : IRequestHandler<LoginCommand, LoginCommandResultDto>
{
    private readonly IAdminAccessTokenFactory _adminAccessTokenFactory;
    private readonly AdminAuthOptions _adminAuthOptions;
    private readonly TimeProvider _timeProvider;

    public LoginCommandHandler(
        IAdminAccessTokenFactory adminAccessTokenFactory,
        IOptions<AdminAuthOptions> adminAuthOptions,
        TimeProvider timeProvider)
    {
        _adminAccessTokenFactory = adminAccessTokenFactory;
        _adminAuthOptions = adminAuthOptions.Value;
        _timeProvider = timeProvider;
    }

    public Task<LoginCommandResultDto> Handle(
        LoginCommand request,
        CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();

        if (string.IsNullOrWhiteSpace(request.Password))
        {
            throw new InvalidOperationException("LoginCommand must be validated before handler execution.");
        }

        if (!PasswordsMatch(request.Password, _adminAuthOptions.SharedPassword))
        {
            throw new InvalidAdminCredentialsException("Niepoprawne hasło administracyjne.");
        }

        var result = _adminAccessTokenFactory.CreateToken(_timeProvider.GetUtcNow());
        return Task.FromResult(result);
    }

    private static bool PasswordsMatch(string actualPassword, string expectedPassword)
    {
        var actualBytes = Encoding.UTF8.GetBytes(actualPassword);
        var expectedBytes = Encoding.UTF8.GetBytes(expectedPassword);

        return CryptographicOperations.FixedTimeEquals(actualBytes, expectedBytes);
    }
}
