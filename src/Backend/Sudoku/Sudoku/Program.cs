using Sudoku.Application;
using Sudoku.Application.Examples;
using Sudoku.Configuration;
using Sudoku.Infrastructure;

var builder = WebApplication.CreateBuilder(args);
builder.AddBackendConfiguration(args);

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
    .AddApplication()
    .AddInfrastructure(builder.Configuration);
builder.Services.AddControllers();

var app = builder.Build();

app.MapControllers();

app.Run();
