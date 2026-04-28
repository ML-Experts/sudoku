using Sudoku.Application;
using Sudoku.Application.Auth;
using Sudoku.Application.Examples;
using Sudoku.Configuration;
using Sudoku.Infrastructure;

var builder = WebApplication.CreateBuilder(args);
builder.AddBackendConfiguration(args);

builder.Services
    .AddOptions<AdminAuthOptions>()
    .BindConfiguration(AdminAuthOptions.SectionName)
    .ValidateDataAnnotations()
    .ValidateOnStart();

builder.Services
    .AddOptions<BackendRuntimeOptions>()
    .BindConfiguration(BackendRuntimeOptions.SectionName)
    .ValidateDataAnnotations()
    .ValidateOnStart();

builder.Services
    .AddOptions<ExamplesStorageOptions>()
    .BindConfiguration(ExamplesStorageOptions.SectionName)
    .ValidateDataAnnotations()
    .Validate(
        options => !Path.IsPathRooted(options.UploadsSubdirectory),
        $"{ExamplesStorageOptions.SectionName}:UploadsSubdirectory must be a relative path.")
    .ValidateOnStart();

builder.Services
    .AddOptions<ExamplesUploadOptions>()
    .BindConfiguration(ExamplesUploadOptions.SectionName)
    .ValidateDataAnnotations()
    .ValidateOnStart();

builder.Services
    .AddOptions<ExamplesPreprocessOptions>()
    .BindConfiguration(ExamplesPreprocessOptions.SectionName)
    .ValidateDataAnnotations()
    .ValidateOnStart();

builder.Services
    .AddApplication()
    .AddInfrastructure(builder.Configuration);
builder.Services.AddAdminAuthentication(builder.Configuration);
builder.Services.AddControllers();

var app = builder.Build();

app.UseAuthentication();
app.UseAuthorization();
app.MapControllers();

app.Run();

public partial class Program { }
