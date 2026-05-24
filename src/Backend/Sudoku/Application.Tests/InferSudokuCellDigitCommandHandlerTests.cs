using Microsoft.Extensions.Options;
using Sudoku.Application.Abstractions;
using Sudoku.Application.ModelsActive;
using Sudoku.Application.ModelsRegistry;
using Sudoku.Application.Sudoku;
using Sudoku.Models.Images;

namespace Application.Tests;

public sealed class InferSudokuCellDigitCommandHandlerTests
{
    [Fact]
    public async Task Handle_PassesEmptyCellParametersToMlRequest()
    {
        var mlGateway = new StubMlImageProcessingGateway();
        var handler = new InferSudokuCellDigitCommandHandler(
            mlGateway,
            new StubActiveModelResolver(),
            Options.Create(new SudokuCellsInferenceOptions
            {
                InferenceProfileName = "default-28x28-v1",
                MaxInlineImageSizeBytes = 10 * 1024 * 1024
            }));

        var command = new InferSudokuCellDigitCommand(
            MimeType: "image/png",
            Base64: Convert.ToBase64String([1, 2, 3]),
            EmptyCellDarkPixelRatioThreshold: 0.02,
            EmptyCellInnerMarginRatio: 0.12,
            CenterAreaRatio: 0.5,
            MinComponentAreaRatio: 0.055,
            LineArtifactMinSpanRatio: 0.4,
            LineArtifactMaxThicknessRatio: 0.08);

        await handler.Handle(command, CancellationToken.None);

        Assert.NotNull(mlGateway.LastRequest);
        var request = mlGateway.LastRequest!;
        Assert.Equal(0.02, request.ResolvedConfiguration.EmptyCellDarkPixelRatioThreshold);
        Assert.Equal(0.12, request.ResolvedConfiguration.EmptyCellInnerMarginRatio);
    }

    private sealed class StubMlImageProcessingGateway : IMlImageProcessingGateway
    {
        public InferSudokuCellDigitMlRequestDto? LastRequest { get; private set; }

        public Task<ImageContent> PreprocessBoardAsync(
            ImageContent image,
            CancellationToken cancellationToken = default)
        {
            throw new NotSupportedException();
        }

        public Task<CellsGrid> ExtractCellsAsync(
            ImageContent image,
            CancellationToken cancellationToken = default)
        {
            throw new NotSupportedException();
        }

        public Task<InferSudokuCellDigitMlResultDto> InferDigitAsync(
            InferSudokuCellDigitMlRequestDto request,
            CancellationToken cancellationToken = default)
        {
            LastRequest = request;
            return Task.FromResult(new InferSudokuCellDigitMlResultDto(7));
        }
    }

    private sealed class StubActiveModelResolver : IActiveModelResolver
    {
        public Task<ResolvedActiveModelDto?> ResolveForInferenceAsync(
            CancellationToken cancellationToken = default)
        {
            return Task.FromResult<ResolvedActiveModelDto?>(
                new ResolvedActiveModelDto(
                    Pointer: new ActiveModelPointerDto(
                        ModelName: "model-01",
                        RegistryRelativePath: "models/registry/model-01",
                        SetBy: "test",
                        UpdatedAtUtc: DateTimeOffset.UtcNow),
                    Manifest: new RegistryModelManifestDto(
                        Name: "model-01",
                        DisplayName: "Model 01",
                        SourceType: "bootstrap",
                        SourceRunName: null,
                        ParentModelName: null,
                        TrainingMode: "inference",
                        Framework: "pytorch",
                        ArchitectureType: "cnn",
                        ArchitectureFamily: "cnn",
                        ArchitectureNumClasses: 10,
                        ArchitectureInputChannels: 1,
                        ArchitectureInputHeight: 28,
                        ArchitectureInputWidth: 28,
                        InputProfile: "default-28x28-v1",
                        TrainingProfileName: null,
                        AugmentationProfileName: null,
                        CreatedAtUtc: DateTimeOffset.UtcNow,
                        CanStartTraining: true,
                        CanUseForInference: true,
                        PrimaryArtifactRelativePath: "artifacts/model.pt",
                        ArtifactFormat: "pt",
                        Warnings: []),
                    ManifestPath: "/tmp/model.json",
                    PrimaryArtifactPath: "/tmp/model.pt"));
        }
    }
}
