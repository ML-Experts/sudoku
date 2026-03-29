using Sudoku.Application;
using Sudoku.Configuration;
using Sudoku.Endpoints;
using Sudoku.Infrastructure;

var builder = WebApplication.CreateBuilder(args);
builder.AddBackendConfiguration(args);

builder.Services
    .AddOptions<BackendRuntimeOptions>()
    .BindConfiguration(BackendRuntimeOptions.SectionName)
    .ValidateDataAnnotations()
    .ValidateOnStart();

builder.Services
    .AddApplication()
    .AddInfrastructure(builder.Configuration);

var app = builder.Build();

app.MapPingEndpoints();

app.Run();
