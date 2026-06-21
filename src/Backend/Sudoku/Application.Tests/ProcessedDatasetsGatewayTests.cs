using System.Text;
using System.Text.Json;
using Microsoft.Extensions.Options;
using Sudoku.Application.Abstractions;
using Sudoku.Application.Datasets;
using Sudoku.Application.Storage;
using Sudoku.Infrastructure.Storage;

namespace Application.Tests;

public sealed class ProcessedDatasetsGatewayTests
{
    [Fact]
    public async Task SaveMetadataAsync_SerializesPreparationName()
    {
        var fileStorageGateway = new InMemoryFileStorageGateway();
        var gateway = new ProcessedDatasetsGateway(
            fileStorageGateway,
            Options.Create(new DatasetsPreparationOptions
            {
                BoardsSubdirectory = "board",
                DigitsSubdirectory = "digit",
                PreparationsDirectoryPath = "/data/preparations",
                ProcessedDatasetsDirectoryPath = "/data/processed",
                TemporaryArtifactsDirectoryPath = "/data/tmp",
                DefaultPreprocessingProfile = "default-28x28-v1",
                DefaultMixSplitRatios = new DatasetsPreparationOptions.MixSplitRatiosOptions()
            }));

        await gateway.SaveMetadataAsync(
            new ProcessedDatasetMetadataDto(
                Name: "digits-v2",
                PreparationName: "preparation-001",
                FileName: "digits-v2.npz",
                PreprocessingProfile: "default-28x28-v1",
                CreatedAtUtc: DateTimeOffset.Parse("2026-06-20T00:15:00Z"),
                Sources:
                [
                    new SelectedRawDatasetSourceDto("v1_training", "board", ["mix"])
                ],
                SampleCounts: new SplitSampleCountsDto(Train: 10, Val: 2, Test: 1),
                SourceReports:
                [
                    new ProcessedDatasetSourceReportDto("v1_training", "board", 13, 13, 0, 0, [])
                ],
                Warnings: ["ml_warning"]),
            CancellationToken.None);

        var savedFile = Assert.Single(fileStorageGateway.Files);
        Assert.Equal("/data/processed/digits-v2.metadata.json", savedFile.Key);

        using var jsonDocument = JsonDocument.Parse(savedFile.Value);
        Assert.Equal("preparation-001", jsonDocument.RootElement.GetProperty("preparationName").GetString());
        Assert.Equal("digits-v2", jsonDocument.RootElement.GetProperty("name").GetString());
    }

    private sealed class InMemoryFileStorageGateway : IFileStorageGateway
    {
        public Dictionary<string, string> Files { get; } = new(StringComparer.Ordinal);

        public async Task SaveAsync(
            string directoryPath,
            string fileName,
            Stream content,
            CancellationToken cancellationToken = default)
        {
            using var reader = new StreamReader(content, Encoding.UTF8, leaveOpen: true);
            var text = await reader.ReadToEndAsync(cancellationToken);
            Files[BuildPath(directoryPath, fileName)] = text;
        }

        public Task ReplaceAsync(
            string directoryPath,
            string fileName,
            Stream content,
            CancellationToken cancellationToken = default)
        {
            throw new NotSupportedException();
        }

        public Task DeleteAsync(
            string directoryPath,
            string fileName,
            CancellationToken cancellationToken = default)
        {
            throw new NotSupportedException();
        }

        public Task DeleteDirectoryAsync(
            string directoryPath,
            string directoryName,
            CancellationToken cancellationToken = default)
        {
            throw new NotSupportedException();
        }

        public Task<Stream> OpenReadAsync(
            string directoryPath,
            string fileName,
            CancellationToken cancellationToken = default)
        {
            throw new NotSupportedException();
        }

        public Task<bool> FileExistsAsync(
            string directoryPath,
            string fileName,
            CancellationToken cancellationToken = default)
        {
            throw new NotSupportedException();
        }

        public Task<IReadOnlyList<StoredFileMetadataDto>> ListFilesAsync(
            string directoryPath,
            CancellationToken cancellationToken = default)
        {
            throw new NotSupportedException();
        }

        public Task<IReadOnlyList<StoredDirectoryMetadataDto>> ListDirectoriesAsync(
            string directoryPath,
            CancellationToken cancellationToken = default)
        {
            throw new NotSupportedException();
        }

        private static string BuildPath(string directoryPath, string fileName)
        {
            return $"{directoryPath.TrimEnd('/')}/{fileName}";
        }
    }
}
