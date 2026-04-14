using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using Microsoft.Extensions.Options;
using Sudoku.Application.Auth;

namespace Sudoku.Infrastructure.Auth;

public sealed class JwtAdminAccessTokenFactory : IAdminAccessTokenFactory
{
    private static readonly JsonSerializerOptions SerializerOptions =
        new(JsonSerializerDefaults.Web);

    private readonly AdminAuthOptions _adminAuthOptions;

    public JwtAdminAccessTokenFactory(IOptions<AdminAuthOptions> adminAuthOptions)
    {
        _adminAuthOptions = adminAuthOptions.Value;
    }

    public LoginCommandResultDto CreateToken(DateTimeOffset issuedAtUtc)
    {
        var expiresAtUtc = issuedAtUtc.AddMinutes(_adminAuthOptions.TokenLifetimeMinutes);
        var unsignedToken = string.Join(
            ".",
            CreateHeaderSegment(),
            CreatePayloadSegment(issuedAtUtc, expiresAtUtc));
        var signatureSegment = CreateSignatureSegment(unsignedToken);
        var accessToken = string.Join(".", unsignedToken, signatureSegment);

        return new LoginCommandResultDto(
            AccessToken: accessToken,
            TokenType: "Bearer",
            ExpiresAtUtc: expiresAtUtc);
    }

    private static string CreateHeaderSegment()
    {
        return Base64UrlEncode(JsonSerializer.SerializeToUtf8Bytes(
            new JwtHeader(Alg: "HS256", Typ: "JWT"),
            SerializerOptions));
    }

    private static string CreatePayloadSegment(
        DateTimeOffset issuedAtUtc,
        DateTimeOffset expiresAtUtc)
    {
        return Base64UrlEncode(JsonSerializer.SerializeToUtf8Bytes(
            new JwtPayload(
                Sub: "admin",
                Jti: Guid.NewGuid().ToString("N"),
                Iat: issuedAtUtc.ToUnixTimeSeconds(),
                Nbf: issuedAtUtc.ToUnixTimeSeconds(),
                Exp: expiresAtUtc.ToUnixTimeSeconds()),
            SerializerOptions));
    }

    private string CreateSignatureSegment(string unsignedToken)
    {
        using var hmac = new HMACSHA256(Encoding.UTF8.GetBytes(_adminAuthOptions.JwtSigningKey));
        var signatureBytes = hmac.ComputeHash(Encoding.ASCII.GetBytes(unsignedToken));
        return Base64UrlEncode(signatureBytes);
    }

    private static string Base64UrlEncode(byte[] bytes)
    {
        return Convert.ToBase64String(bytes)
            .TrimEnd('=')
            .Replace('+', '-')
            .Replace('/', '_');
    }

    private sealed record JwtHeader(string Alg, string Typ);

    private sealed record JwtPayload(
        string Sub,
        string Jti,
        long Iat,
        long Nbf,
        long Exp);
}
