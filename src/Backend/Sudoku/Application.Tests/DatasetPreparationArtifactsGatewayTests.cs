using Microsoft.Extensions.Options;
using Sudoku.Application.Datasets;
using Sudoku.Infrastructure.Storage;

namespace Application.Tests;

public sealed class DatasetPreparationArtifactsGatewayTests
{
    [Fact]
    public async Task GetSourceFolderNamesAsync_ReadsManifestFromProcessedPreparationsFallback()
    {
        var tempDirectory = Directory.CreateTempSubdirectory();
        try
        {
            var preparationsDirectoryPath = Path.Combine(tempDirectory.FullName, "preparations");
            var processedDatasetsDirectoryPath = Path.Combine(tempDirectory.FullName, "processed");
            var manifestDirectoryPath = Path.Combine(
                processedDatasetsDirectoryPath,
                "preparations",
                "preparation-001",
                "digit");

            Directory.CreateDirectory(manifestDirectoryPath);
            await File.WriteAllTextAsync(
                Path.Combine(manifestDirectoryPath, "folders.json"),
                """
                ["mnist_train","mnist_test"]
                """);

            var gateway = CreateGateway(preparationsDirectoryPath, processedDatasetsDirectoryPath);

            var result = await gateway.GetSourceFolderNamesAsync("preparation-001", "digit");

            Assert.Equal(["mnist_train", "mnist_test"], result);
        }
        finally
        {
            tempDirectory.Delete(recursive: true);
        }
    }

    [Fact]
    public async Task GetBoardFileNamesAsync_ReadsManifestFromProcessedPreparationsFallback()
    {
        var tempDirectory = Directory.CreateTempSubdirectory();
        try
        {
            var preparationsDirectoryPath = Path.Combine(tempDirectory.FullName, "preparations");
            var processedDatasetsDirectoryPath = Path.Combine(tempDirectory.FullName, "processed");
            var manifestDirectoryPath = Path.Combine(
                processedDatasetsDirectoryPath,
                "preparations",
                "preparation-001",
                "board",
                "v1_training");

            Directory.CreateDirectory(manifestDirectoryPath);
            await File.WriteAllTextAsync(
                Path.Combine(manifestDirectoryPath, "file.json"),
                """
                ["Image1","Image2"]
                """);

            var gateway = CreateGateway(preparationsDirectoryPath, processedDatasetsDirectoryPath);

            var result = await gateway.GetBoardFileNamesAsync("preparation-001", "v1_training");

            Assert.Equal(["Image1", "Image2"], result);
        }
        finally
        {
            tempDirectory.Delete(recursive: true);
        }
    }

    private static DatasetPreparationArtifactsGateway CreateGateway(
        string preparationsDirectoryPath,
        string processedDatasetsDirectoryPath)
    {
        return new DatasetPreparationArtifactsGateway(
            new LocalFileStorageGateway(),
            Options.Create(new DatasetsPreparationOptions
            {
                BoardsSubdirectory = "/tmp/raw/boards",
                DigitsSubdirectory = "/tmp/raw/digits",
                PreparationsDirectoryPath = preparationsDirectoryPath,
                ProcessedDatasetsDirectoryPath = processedDatasetsDirectoryPath,
                TemporaryArtifactsDirectoryPath = "/tmp/datasets-temp",
                DefaultPreprocessingProfile = "default-28x28-v1",
                DefaultMixSplitRatios = new DatasetsPreparationOptions.MixSplitRatiosOptions()
            }));
    }
}
