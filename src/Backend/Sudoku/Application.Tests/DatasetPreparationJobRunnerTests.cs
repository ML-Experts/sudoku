using Sudoku.Application.Abstractions;
using Sudoku.Application.Datasets;
using Sudoku.Application.Ml;

namespace Application.Tests;

public sealed class DatasetPreparationJobRunnerTests
{
    private static readonly DateTimeOffset FixedNow = DateTimeOffset.Parse("2026-06-19T19:12:00Z");

    [Fact]
    public async Task RunAsync_TransitionsFromQueuedToCompleted_WhenMlSucceeds()
    {
        var gateway = new InMemoryDatasetPreparationsGateway(CreateQueuedMetadata());
        var mlGateway = new StubMlDatasetPreparationsGateway(new CreateDatasetPreparationMlResultDto(
            PreparationName: "preparation-001",
            CreatedAtUtc: FixedNow,
            Status: "succeeded",
            SourceReports:
            [
                new DatasetPreparationMlSourceReportDto("v1_training", "board", 24, 2, 3),
                new DatasetPreparationMlSourceReportDto("mnist_train", "digit", 110, 4, 0)
            ],
            Warnings: ["ml_warning"]));
        var runner = CreateRunner(gateway, mlGateway);

        await runner.RunAsync("preparation-001", CancellationToken.None);

        var metadata = gateway.Items["preparation-001"];
        Assert.Equal("completed", metadata.Status);
        Assert.Equal(FixedNow, metadata.StartedAtUtc);
        Assert.Equal(FixedNow, metadata.FinishedAtUtc);
        Assert.Contains("ml_warning", metadata.Warnings);
        Assert.Contains("ml_preparation_status_mismatch", metadata.Warnings);
        Assert.Equal(24, metadata.SourceReports[0].PreparedItemsCount);
        Assert.Equal(110, metadata.SourceReports[1].PreparedItemsCount);
    }

    [Fact]
    public async Task RunAsync_MarksPreparationAsFailed_WhenMlOmitsSourceReport()
    {
        var gateway = new InMemoryDatasetPreparationsGateway(CreateQueuedMetadata());
        var mlGateway = new StubMlDatasetPreparationsGateway(new CreateDatasetPreparationMlResultDto(
            PreparationName: "preparation-001",
            CreatedAtUtc: FixedNow,
            Status: "completed",
            SourceReports:
            [
                new DatasetPreparationMlSourceReportDto("v1_training", "board", 24, 2, 3)
            ],
            Warnings: []));
        var runner = CreateRunner(gateway, mlGateway);

        await runner.RunAsync("preparation-001", CancellationToken.None);

        var metadata = gateway.Items["preparation-001"];
        Assert.Equal("failed", metadata.Status);
        Assert.Equal(CreateDatasetPreparationErrorTypes.PreparationInvariantViolation, metadata.FailureErrorType);
        Assert.Contains("mnist_train", metadata.FailureMessage);
    }

    [Fact]
    public async Task RunAsync_AddsCleanupWarning_WhenCleanupFailsAfterMlError()
    {
        var gateway = new InMemoryDatasetPreparationsGateway(CreateQueuedMetadata())
        {
            CleanupException = new IOException("cleanup failed")
        };
        var mlGateway = new StubMlDatasetPreparationsGateway(
            new MlServiceUnavailableException("Serwis ML jest niedostępny."));
        var runner = CreateRunner(gateway, mlGateway);

        await runner.RunAsync("preparation-001", CancellationToken.None);

        var metadata = gateway.Items["preparation-001"];
        Assert.Equal("failed", metadata.Status);
        Assert.Equal(CreateDatasetPreparationErrorTypes.MlUnavailable, metadata.FailureErrorType);
        Assert.Contains(CreateDatasetPreparationErrorTypes.PreparationCleanupPartial, metadata.Warnings);
    }

    private static DatasetPreparationJobRunner CreateRunner(
        InMemoryDatasetPreparationsGateway? gateway = null,
        StubMlDatasetPreparationsGateway? mlGateway = null)
    {
        return new DatasetPreparationJobRunner(
            gateway ?? new InMemoryDatasetPreparationsGateway(CreateQueuedMetadata()),
            mlGateway ?? new StubMlDatasetPreparationsGateway(new CreateDatasetPreparationMlResultDto(
                PreparationName: "preparation-001",
                CreatedAtUtc: FixedNow,
                Status: "completed",
                SourceReports: [],
                Warnings: [])),
            new FixedTimeProvider(FixedNow));
    }

    private static DatasetPreparationMetadataDto CreateQueuedMetadata()
    {
        return new DatasetPreparationMetadataDto(
            PreparationName: "preparation-001",
            Status: "queued",
            CreatedAtUtc: FixedNow,
            UpdatedAtUtc: FixedNow,
            StartedAtUtc: null,
            FinishedAtUtc: null,
            Sources:
            [
                new CreateDatasetPreparationSourceDto("v1_training", "board"),
                new CreateDatasetPreparationSourceDto("mnist_train", "digit")
            ],
            SourceReports:
            [
                new DatasetPreparationSourceReportDto("v1_training", "board", 0, 0, 0),
                new DatasetPreparationSourceReportDto("mnist_train", "digit", 0, 0, 0)
            ],
            Warnings: [],
            FailureErrorType: null,
            FailureMessage: null);
    }

    private sealed class InMemoryDatasetPreparationsGateway : IDatasetPreparationsGateway
    {
        public InMemoryDatasetPreparationsGateway(DatasetPreparationMetadataDto metadata)
        {
            Items[metadata.PreparationName] = metadata;
        }

        public Dictionary<string, DatasetPreparationMetadataDto> Items { get; } = new(StringComparer.Ordinal);

        public Exception? CleanupException { get; init; }

        public Task<IReadOnlyList<DatasetPreparationMetadataDto>> ListAsync(CancellationToken cancellationToken = default)
        {
            return Task.FromResult<IReadOnlyList<DatasetPreparationMetadataDto>>(Items.Values.ToArray());
        }

        public Task<DatasetPreparationMetadataDto?> GetByNameAsync(
            string preparationName,
            CancellationToken cancellationToken = default)
        {
            Items.TryGetValue(preparationName, out var metadata);
            return Task.FromResult(metadata);
        }

        public Task<bool> TryCreateAsync(
            DatasetPreparationMetadataDto metadata,
            CancellationToken cancellationToken = default)
        {
            Items[metadata.PreparationName] = metadata;
            return Task.FromResult(true);
        }

        public Task UpdateAsync(
            DatasetPreparationMetadataDto metadata,
            CancellationToken cancellationToken = default)
        {
            Items[metadata.PreparationName] = metadata;
            return Task.CompletedTask;
        }

        public Task CleanupGeneratedContentAsync(
            string preparationName,
            CancellationToken cancellationToken = default)
        {
            if (CleanupException is not null)
            {
                throw CleanupException;
            }

            Items.Remove(preparationName);
            return Task.CompletedTask;
        }
    }

    private sealed class StubMlDatasetPreparationsGateway : IMlDatasetPreparationsGateway
    {
        private readonly CreateDatasetPreparationMlResultDto? _result;
        private readonly Exception? _exception;

        public StubMlDatasetPreparationsGateway(CreateDatasetPreparationMlResultDto result)
        {
            _result = result;
        }

        public StubMlDatasetPreparationsGateway(Exception exception)
        {
            _exception = exception;
        }

        public Task<CreateDatasetPreparationMlResultDto> CreateAsync(
            CreateDatasetPreparationMlRequestDto request,
            CancellationToken cancellationToken = default)
        {
            if (_exception is not null)
            {
                throw _exception;
            }

            return Task.FromResult(_result!);
        }
    }

    private sealed class FixedTimeProvider : TimeProvider
    {
        private readonly DateTimeOffset _utcNow;

        public FixedTimeProvider(DateTimeOffset utcNow)
        {
            _utcNow = utcNow;
        }

        public override DateTimeOffset GetUtcNow()
        {
            return _utcNow;
        }
    }
}
