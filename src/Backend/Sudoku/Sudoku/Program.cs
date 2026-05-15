using System.Text.Json;
using Sudoku.Application;
using Sudoku.Application.Abstractions;
using Sudoku.Application.Auth;
using Sudoku.Application.Datasets;
using Sudoku.Application.Examples;
using Sudoku.Application.ModelsActive;
using Sudoku.Application.ModelsRegistry;
using Sudoku.Application.Sudoku;
using Sudoku.Application.Trainings;
using Sudoku.Configuration;
using Sudoku.Hubs;
using Sudoku.Infrastructure;
using Sudoku.Realtime;

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
    .AddOptions<SudokuCellsInferenceOptions>()
    .BindConfiguration(SudokuCellsInferenceOptions.SectionName)
    .ValidateDataAnnotations()
    .Validate(
        options => !string.IsNullOrWhiteSpace(options.InferenceProfileName),
        $"{SudokuCellsInferenceOptions.SectionName}:InferenceProfileName is required.")
    .ValidateOnStart();

builder.Services
    .AddOptions<RawDatasetsStorageOptions>()
    .BindConfiguration(RawDatasetsStorageOptions.SectionName)
    .ValidateDataAnnotations()
    .Validate(
        options => Path.IsPathRooted(options.BoardsSubdirectory),
        $"{RawDatasetsStorageOptions.SectionName}:BoardsSubdirectory must be an absolute path.")
    .Validate(
        options => Path.IsPathRooted(options.DigitsSubdirectory),
        $"{RawDatasetsStorageOptions.SectionName}:DigitsSubdirectory must be an absolute path.")
    .ValidateOnStart();

builder.Services
    .AddOptions<DatasetsPreparationOptions>()
    .BindConfiguration(DatasetsPreparationOptions.SectionName)
    .ValidateDataAnnotations()
    .Validate(
        options => Path.IsPathRooted(options.BoardsSubdirectory),
        $"{DatasetsPreparationOptions.SectionName}:BoardsSubdirectory must be an absolute path.")
    .Validate(
        options => Path.IsPathRooted(options.DigitsSubdirectory),
        $"{DatasetsPreparationOptions.SectionName}:DigitsSubdirectory must be an absolute path.")
    .Validate(
        options => Path.IsPathRooted(options.ProcessedDatasetsDirectoryPath),
        $"{DatasetsPreparationOptions.SectionName}:ProcessedDatasetsDirectoryPath must be an absolute path.")
    .Validate(
        options => Path.IsPathRooted(options.TemporaryArtifactsDirectoryPath),
        $"{DatasetsPreparationOptions.SectionName}:TemporaryArtifactsDirectoryPath must be an absolute path.")
    .Validate(
        options => !string.IsNullOrWhiteSpace(options.DefaultPreprocessingProfile),
        $"{DatasetsPreparationOptions.SectionName}:DefaultPreprocessingProfile is required.")
    .Validate(
        options => Math.Abs(
            options.DefaultMixSplitRatios.Train
            + options.DefaultMixSplitRatios.Val
            + options.DefaultMixSplitRatios.Test
            - 1d) <= 0.0001d,
        $"{DatasetsPreparationOptions.SectionName}:DefaultMixSplitRatios must sum to 1.0.")
    .ValidateOnStart();

builder.Services
    .AddOptions<TrainingsStorageOptions>()
    .BindConfiguration(TrainingsStorageOptions.SectionName)
    .ValidateDataAnnotations()
    .Validate(
        options => Path.IsPathRooted(options.RunsDirectoryPath),
        $"{TrainingsStorageOptions.SectionName}:RunsDirectoryPath must be an absolute path.")
    .Validate(
        options => Path.IsPathRooted(options.ReportsDirectoryPath),
        $"{TrainingsStorageOptions.SectionName}:ReportsDirectoryPath must be an absolute path.")
    .Validate(
        options => Path.IsPathRooted(options.MetadataDirectoryPath),
        $"{TrainingsStorageOptions.SectionName}:MetadataDirectoryPath must be an absolute path.")
    .Validate(
        options => Path.IsPathRooted(options.WorkingDirectoryPath),
        $"{TrainingsStorageOptions.SectionName}:WorkingDirectoryPath must be an absolute path.")
    .ValidateOnStart();

builder.Services
    .AddOptions<ModelsRegistryStorageOptions>()
    .BindConfiguration(ModelsRegistryStorageOptions.SectionName)
    .ValidateDataAnnotations()
    .Validate(
        options => Path.IsPathRooted(options.RegistryDirectoryPath),
        $"{ModelsRegistryStorageOptions.SectionName}:RegistryDirectoryPath must be an absolute path.")
    .ValidateOnStart();

builder.Services
    .AddOptions<ModelsActiveStorageOptions>()
    .BindConfiguration(ModelsActiveStorageOptions.SectionName)
    .ValidateDataAnnotations()
    .Validate(
        options => Path.IsPathRooted(options.ActiveDirectoryPath),
        $"{ModelsActiveStorageOptions.SectionName}:ActiveDirectoryPath must be an absolute path.")
    .ValidateOnStart();

builder.Services
    .AddOptions<TrainingDefaultsOptions>()
    .BindConfiguration(TrainingDefaultsOptions.SectionName)
    .ValidateDataAnnotations()
    .Validate(
        options => !string.IsNullOrWhiteSpace(options.RunNamePrefix),
        $"{TrainingDefaultsOptions.SectionName}:RunNamePrefix is required.")
    .Validate(
        options => !string.IsNullOrWhiteSpace(options.TrainingMode),
        $"{TrainingDefaultsOptions.SectionName}:TrainingMode is required.")
    .Validate(
        options => !string.IsNullOrWhiteSpace(options.TrainingProfileName),
        $"{TrainingDefaultsOptions.SectionName}:TrainingProfileName is required.")
    .Validate(
        options => !string.IsNullOrWhiteSpace(options.AugmentationProfileName),
        $"{TrainingDefaultsOptions.SectionName}:AugmentationProfileName is required.")
    .Validate(
        options => !string.IsNullOrWhiteSpace(options.BenchmarkName),
        $"{TrainingDefaultsOptions.SectionName}:BenchmarkName is required.")
    .ValidateOnStart();

builder.Services
    .AddApplication()
    .AddInfrastructure(builder.Configuration);
builder.Services.AddSingleton<ITrainingRunEventPublisher, SignalRTrainingRunEventPublisher>();
builder.Services.AddAdminAuthentication(builder.Configuration);
builder.Services.AddControllers();
builder.Services
    .AddSignalR()
    .AddJsonProtocol(options =>
    {
        options.PayloadSerializerOptions.PropertyNamingPolicy = JsonNamingPolicy.CamelCase;
    });

var app = builder.Build();

app.UseAuthentication();
app.UseAuthorization();
app.MapControllers();
app.MapHub<TrainingRunHub>("/ws/trainings/{runName}");

app.Run();

public partial class Program { }
