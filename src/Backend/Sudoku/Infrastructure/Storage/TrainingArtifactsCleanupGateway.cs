using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using Sudoku.Application.Abstractions;
using Sudoku.Application.ModelsRegistry;
using Sudoku.Application.Trainings;

namespace Sudoku.Infrastructure.Storage;

public sealed class TrainingArtifactsCleanupGateway : ITrainingArtifactsCleanupGateway
{
    private readonly IFileStorageGateway _fileStorageGateway;
    private readonly TrainingsStorageOptions _trainingsStorageOptions;
    private readonly ModelsRegistryStorageOptions _modelsRegistryStorageOptions;
    private readonly ILogger<TrainingArtifactsCleanupGateway> _logger;

    public TrainingArtifactsCleanupGateway(
        IFileStorageGateway fileStorageGateway,
        IOptions<TrainingsStorageOptions> trainingsStorageOptions,
        IOptions<ModelsRegistryStorageOptions> modelsRegistryStorageOptions,
        ILogger<TrainingArtifactsCleanupGateway> logger)
    {
        _fileStorageGateway = fileStorageGateway;
        _trainingsStorageOptions = trainingsStorageOptions.Value;
        _modelsRegistryStorageOptions = modelsRegistryStorageOptions.Value;
        _logger = logger;
    }

    public async Task<IReadOnlyList<string>> CleanupFailedOrCancelledRunAsync(
        TrainingRunMetadataDto metadata,
        CancellationToken cancellationToken = default)
    {
        var warnings = new List<string>();

        await TryDeleteDirectoryAsync(
            _trainingsStorageOptions.RunsDirectoryPath,
            metadata.RunName,
            "training_run_artifacts_cleanup_failed",
            warnings,
            cancellationToken);

        await TryDeleteDirectoryAsync(
            _trainingsStorageOptions.ReportsDirectoryPath,
            metadata.RunName,
            "training_report_cleanup_failed",
            warnings,
            cancellationToken);

        await TryDeleteDirectoryAsync(
            _trainingsStorageOptions.WorkingDirectoryPath,
            metadata.RunName,
            "training_workdir_cleanup_failed",
            warnings,
            cancellationToken);

        await TryDeleteDirectoryAsync(
            _modelsRegistryStorageOptions.RegistryDirectoryPath,
            metadata.ProducedModelName,
            "produced_model_cleanup_failed",
            warnings,
            cancellationToken);

        return warnings.Distinct(StringComparer.Ordinal).ToArray();
    }

    private async Task TryDeleteDirectoryAsync(
        string parentDirectoryPath,
        string directoryName,
        string warning,
        ICollection<string> warnings,
        CancellationToken cancellationToken)
    {
        try
        {
            await _fileStorageGateway.DeleteDirectoryAsync(parentDirectoryPath, directoryName, cancellationToken);
        }
        catch (Exception exception) when (exception is IOException
                                         or UnauthorizedAccessException
                                         or InvalidOperationException)
        {
            warnings.Add(warning);
            _logger.LogError(
                exception,
                "Nie udało się usunąć katalogu artefaktów treningu {DirectoryName}.",
                directoryName);
        }
    }
}
