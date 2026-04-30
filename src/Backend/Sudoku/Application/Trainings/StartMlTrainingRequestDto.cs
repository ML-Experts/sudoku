namespace Sudoku.Application.Trainings;

public sealed record StartMlTrainingRequestDto(
    string RunName,
    StartMlTrainingBaseModelDto BaseModel,
    StartMlTrainingProcessedDatasetDto ProcessedDataset,
    ResolvedTrainingConfigurationDto ResolvedConfiguration,
    OutputRegistryModelDto OutputModel,
    TrainingOutputPathsDto OutputPaths);

public sealed record StartMlTrainingBaseModelDto(
    string Name,
    string DirectoryPath,
    string ManifestPath,
    string PrimaryArtifactPath,
    string InputProfile,
    string SourceType);

public sealed record StartMlTrainingProcessedDatasetDto(
    string Name,
    string FilePath,
    string PreprocessingProfile);

public sealed record ResolvedTrainingConfigurationDto(
    string TrainingMode,
    string TrainingProfileName,
    string AugmentationProfileName,
    string BenchmarkName,
    int Seed);

public sealed record OutputRegistryModelDto(
    string Name,
    string DirectoryPath);

public sealed record TrainingOutputPathsDto(
    string RunDirectoryPath,
    string ReportDirectoryPath,
    string BenchmarkDirectoryPath,
    string TemporaryWorkingDirectoryPath);
