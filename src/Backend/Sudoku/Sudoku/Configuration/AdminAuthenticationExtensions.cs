using System.Text;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.IdentityModel.Tokens;
using Sudoku.Application.Auth;
using Sudoku.Contracts;

namespace Sudoku.Configuration;

public static class AdminAuthenticationExtensions
{
    private const string AuthErrorTypeItemKey = "AdminAuthErrorType";
    private const string AuthErrorMessageItemKey = "AdminAuthErrorMessage";

    public static IServiceCollection AddAdminAuthentication(
        this IServiceCollection services,
        IConfiguration configuration)
    {
        var adminAuthOptions = configuration
            .GetSection(AdminAuthOptions.SectionName)
            .Get<AdminAuthOptions>()
            ?? new AdminAuthOptions();
        var signingKey = new SymmetricSecurityKey(
            Encoding.UTF8.GetBytes(adminAuthOptions.JwtSigningKey));

        services
            .AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
            .AddJwtBearer(options =>
            {
                options.TokenValidationParameters = new TokenValidationParameters
                {
                    ValidateIssuer = false,
                    ValidateAudience = false,
                    ValidateIssuerSigningKey = true,
                    IssuerSigningKey = signingKey,
                    ValidateLifetime = true,
                    RequireExpirationTime = true,
                    ClockSkew = TimeSpan.Zero
                };
                options.Events = new JwtBearerEvents
                {
                    OnAuthenticationFailed = context =>
                    {
                        if (context.Exception is SecurityTokenExpiredException)
                        {
                            SetAuthError(
                                context.HttpContext,
                                AdminAuthErrorTypes.AdminTokenExpired,
                                "Sesja administracyjna wygasła. Zaloguj się ponownie.");
                        }
                        else
                        {
                            SetAuthError(
                                context.HttpContext,
                                AdminAuthErrorTypes.AdminTokenInvalid,
                                "Wymagany jest poprawny token administracyjny.");
                        }

                        return Task.CompletedTask;
                    },
                    OnChallenge = async context =>
                    {
                        if (context.Response.HasStarted)
                        {
                            return;
                        }

                        context.HandleResponse();
                        context.Response.StatusCode = StatusCodes.Status401Unauthorized;

                        await context.Response.WriteAsJsonAsync(
                            ResolveErrorResponse(context.HttpContext));
                    }
                };
            });

        services.AddAuthorization();
        return services;
    }

    private static void SetAuthError(
        HttpContext httpContext,
        string errorType,
        string message)
    {
        httpContext.Items[AuthErrorTypeItemKey] = errorType;
        httpContext.Items[AuthErrorMessageItemKey] = message;
    }

    private static ErrorApiResponse ResolveErrorResponse(HttpContext httpContext)
    {
        var errorType = httpContext.Items.TryGetValue(AuthErrorTypeItemKey, out var rawErrorType)
            ? rawErrorType as string
            : null;
        var message = httpContext.Items.TryGetValue(AuthErrorMessageItemKey, out var rawMessage)
            ? rawMessage as string
            : null;

        return new ErrorApiResponse(
            ErrorType: errorType ?? AdminAuthErrorTypes.AdminTokenInvalid,
            Message: message ?? "Wymagany jest poprawny token administracyjny.");
    }
}
