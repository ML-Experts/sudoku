using Sudoku.Application.Trainings;

namespace Application.Tests;

public sealed class CreateTrainingRunCommandValidatorTests
{
    private readonly CreateTrainingRunCommandValidator _validator = new();

    [Fact]
    public void Validate_ReturnsNoErrors_ForValidTrainingParameters()
    {
        var command = CreateCommand();

        var result = _validator.Validate(command);

        Assert.True(result.IsValid);
    }

    [Fact]
    public void Validate_ReturnsInvalidRequest_WhenTrainingParametersAreMissing()
    {
        var result = _validator.Validate(new CreateTrainingRunCommand(
            BaseModelName: "cnn-bootstrap",
            ProcessedDatasetName: "digits-v1",
            TrainingParameters: null));

        var failure = Assert.Single(result.Errors);
        Assert.Equal(CreateTrainingRunErrorTypes.InvalidRequest, failure.ErrorCode);
        Assert.Equal("TrainingParameters", failure.PropertyName);
    }

    [Theory]
    [InlineData(0)]
    [InlineData(-1)]
    public void Validate_ReturnsInvalidRequest_WhenEpochsAreNotPositive(int epochs)
    {
        var result = _validator.Validate(CreateCommand(
            trainingParameters: CreateTrainingParameters(Epochs: epochs)));

        var failure = Assert.Single(result.Errors);
        Assert.Equal(CreateTrainingRunErrorTypes.InvalidRequest, failure.ErrorCode);
        Assert.Equal("TrainingParameters.Epochs", failure.PropertyName);
    }

    [Theory]
    [InlineData("unsupported")]
    [InlineData(" ")]
    public void Validate_ReturnsInvalidRequest_WhenFineTuningPolicyIsUnsupported(string policy)
    {
        var result = _validator.Validate(CreateCommand(
            trainingParameters: CreateTrainingParameters(FineTuningPolicy: policy)));

        var failure = Assert.Single(result.Errors);
        Assert.Equal(CreateTrainingRunErrorTypes.InvalidRequest, failure.ErrorCode);
        Assert.Equal("TrainingParameters.FineTuningPolicy", failure.PropertyName);
    }

    [Fact]
    public void Validate_ReturnsNoErrors_WhenUseBestCheckpointIsMissing()
    {
        var result = _validator.Validate(CreateCommand(
            trainingParameters: CreateTrainingParameters(UseBestCheckpoint: null)));

        Assert.True(result.IsValid);
    }

    [Fact]
    public void Validate_ReturnsNoErrors_WhenEarlyStoppingMinDeltaIsMissing()
    {
        var result = _validator.Validate(CreateCommand(
            trainingParameters: CreateTrainingParameters(EarlyStoppingMinDelta: null)));

        Assert.True(result.IsValid);
    }

    [Fact]
    public void Validate_ReturnsNoErrors_WhenWarmupEpochsIsMissing()
    {
        var result = _validator.Validate(CreateCommand(
            trainingParameters: CreateTrainingParameters(WarmupEpochs: null)));

        Assert.True(result.IsValid);
    }

    [Theory]
    [InlineData(-0.0001)]
    [InlineData(-1)]
    public void Validate_ReturnsInvalidRequest_WhenEarlyStoppingMinDeltaIsNegative(
        double earlyStoppingMinDelta)
    {
        var result = _validator.Validate(CreateCommand(
            trainingParameters: CreateTrainingParameters(
                EarlyStoppingMinDelta: earlyStoppingMinDelta)));

        var failure = Assert.Single(result.Errors);
        Assert.Equal(CreateTrainingRunErrorTypes.InvalidRequest, failure.ErrorCode);
        Assert.Equal("TrainingParameters.EarlyStoppingMinDelta", failure.PropertyName);
    }

    [Theory]
    [InlineData(-1)]
    [InlineData(-3)]
    public void Validate_ReturnsInvalidRequest_WhenWarmupEpochsIsNegative(int warmupEpochs)
    {
        var result = _validator.Validate(CreateCommand(
            trainingParameters: CreateTrainingParameters(WarmupEpochs: warmupEpochs)));

        var failure = Assert.Single(result.Errors);
        Assert.Equal(CreateTrainingRunErrorTypes.InvalidRequest, failure.ErrorCode);
        Assert.Equal("TrainingParameters.WarmupEpochs", failure.PropertyName);
    }

    private static CreateTrainingRunCommand CreateCommand(
        string? baseModelName = "cnn-bootstrap",
        string? processedDatasetName = "digits-v1",
        TrainingRunRequestedParametersDto? trainingParameters = null)
    {
        return new CreateTrainingRunCommand(
            BaseModelName: baseModelName,
            ProcessedDatasetName: processedDatasetName,
            TrainingParameters: trainingParameters ?? CreateTrainingParameters());
    }

    private static TrainingRunRequestedParametersDto CreateTrainingParameters(
        int? Epochs = 20,
        double? LearningRate = 0.001,
        int? BatchSize = 32,
        int? EarlyStoppingPatience = 5,
        double? EarlyStoppingMinDelta = 0.001,
        int? WarmupEpochs = 0,
        int? LrSchedulerPatience = 3,
        double? LrSchedulerFactor = 0.5,
        string? FineTuningPolicy = "all",
        bool? UseBestCheckpoint = true)
    {
        return new TrainingRunRequestedParametersDto(
            Epochs: Epochs,
            LearningRate: LearningRate,
            BatchSize: BatchSize,
            EarlyStoppingPatience: EarlyStoppingPatience,
            EarlyStoppingMinDelta: EarlyStoppingMinDelta,
            WarmupEpochs: WarmupEpochs,
            LrSchedulerPatience: LrSchedulerPatience,
            LrSchedulerFactor: LrSchedulerFactor,
            FineTuningPolicy: FineTuningPolicy,
            UseBestCheckpoint: UseBestCheckpoint);
    }
}
