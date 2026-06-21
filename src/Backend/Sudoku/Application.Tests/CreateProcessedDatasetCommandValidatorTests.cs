using Sudoku.Application.Datasets;

namespace Application.Tests;

public sealed class CreateProcessedDatasetCommandValidatorTests
{
    private readonly CreateProcessedDatasetCommandValidator _validator = new();

    [Fact]
    public void Validate_ReturnsError_WhenPreparationNameIsMissing()
    {
        var result = _validator.Validate(new CreateProcessedDatasetCommand(
            PreparationName: " ",
            Name: "digits-v2",
            Sources:
            [
                new SelectedRawDatasetSourceDto("v1_training", "board", ["mix"])
            ]));

        var failure = Assert.Single(result.Errors);
        Assert.Equal(CreateProcessedDatasetErrorTypes.InvalidDatasetPreparationName, failure.ErrorCode);
    }

    [Fact]
    public void Validate_ReturnsError_WhenMixIsCombinedWithOtherSplits()
    {
        var result = _validator.Validate(new CreateProcessedDatasetCommand(
            PreparationName: "preparation-001",
            Name: "digits-v2",
            Sources:
            [
                new SelectedRawDatasetSourceDto("v1_training", "board", ["mix", "train"])
            ]));

        var failure = Assert.Single(result.Errors);
        Assert.Equal(CreateProcessedDatasetErrorTypes.InvalidDatasetSplitSelection, failure.ErrorCode);
    }

    [Fact]
    public void Validate_Succeeds_ForValidPreparationBasedRequest()
    {
        var result = _validator.Validate(new CreateProcessedDatasetCommand(
            PreparationName: "preparation-001",
            Name: "digits-v2",
            Sources:
            [
                new SelectedRawDatasetSourceDto("v1_training", "board", ["mix"]),
                new SelectedRawDatasetSourceDto("mnist_train", "digit", ["train", "val"])
            ]));

        Assert.True(result.IsValid);
    }
}
