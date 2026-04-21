using System.ComponentModel.DataAnnotations;

namespace Sudoku.Application.Auth;

public sealed class AdminAuthOptions
{
    public const string SectionName = "AdminAuth";

    [Required]
    public string SharedPassword { get; init; } = string.Empty;

    [Required]
    [MinLength(32)]
    public string JwtSigningKey { get; init; } = string.Empty;

    [Range(1, 1440)]
    public int TokenLifetimeMinutes { get; init; } = 60;
}
