using Sudoku.Application.Datasets;

namespace Application.Tests;

public sealed class GetDatasetPreparationBoardImageQueryValidatorTests
{
    private readonly GetDatasetPreparationBoardImageQueryValidator _validator = new();

    [Fact]
    public void Validate_ReturnsNoErrors_ForValidRequest()
    {
        var result = _validator.Validate(new GetDatasetPreparationBoardImageQuery(
            PreparationName: "preparation-001",
            SourceName: "v1_training",
            BoardFolderName: "Image1"));

        Assert.True(result.IsValid);
    }

    [Theory]
    [InlineData(null)]
    [InlineData("")]
    [InlineData("   ")]
    public void Validate_ReturnsInvalidPreparationName_WhenPreparationNameIsMissing(string? preparationName)
    {
        var result = _validator.Validate(new GetDatasetPreparationBoardImageQuery(
            PreparationName: preparationName,
            SourceName: "v1_training",
            BoardFolderName: "Image1"));

        var failure = Assert.Single(result.Errors);
        Assert.Equal(GetDatasetPreparationBoardImageErrorTypes.InvalidDatasetPreparationName, failure.ErrorCode);
        Assert.Equal(nameof(GetDatasetPreparationBoardImageQuery.PreparationName), failure.PropertyName);
    }

    [Theory]
    [InlineData("../prep")]
    [InlineData("prep/name")]
    [InlineData("prep\\name")]
    [InlineData("prep:name")]
    public void Validate_ReturnsInvalidPreparationName_WhenPreparationNameContainsForbiddenCharacters(
        string preparationName)
    {
        var result = _validator.Validate(new GetDatasetPreparationBoardImageQuery(
            PreparationName: preparationName,
            SourceName: "v1_training",
            BoardFolderName: "Image1"));

        var failure = Assert.Single(result.Errors);
        Assert.Equal(GetDatasetPreparationBoardImageErrorTypes.InvalidDatasetPreparationName, failure.ErrorCode);
        Assert.Equal(nameof(GetDatasetPreparationBoardImageQuery.PreparationName), failure.PropertyName);
    }

    [Theory]
    [InlineData(null)]
    [InlineData("")]
    [InlineData("   ")]
    public void Validate_ReturnsInvalidSourceName_WhenSourceNameIsMissing(string? sourceName)
    {
        var result = _validator.Validate(new GetDatasetPreparationBoardImageQuery(
            PreparationName: "preparation-001",
            SourceName: sourceName,
            BoardFolderName: "Image1"));

        var failure = Assert.Single(result.Errors);
        Assert.Equal(GetDatasetPreparationBoardImageErrorTypes.InvalidDatasetPreparationSourceName, failure.ErrorCode);
        Assert.Equal(nameof(GetDatasetPreparationBoardImageQuery.SourceName), failure.PropertyName);
    }

    [Theory]
    [InlineData("../source")]
    [InlineData("source/name")]
    [InlineData("source\\name")]
    [InlineData("source:name")]
    public void Validate_ReturnsInvalidSourceName_WhenSourceNameContainsForbiddenCharacters(
        string sourceName)
    {
        var result = _validator.Validate(new GetDatasetPreparationBoardImageQuery(
            PreparationName: "preparation-001",
            SourceName: sourceName,
            BoardFolderName: "Image1"));

        var failure = Assert.Single(result.Errors);
        Assert.Equal(GetDatasetPreparationBoardImageErrorTypes.InvalidDatasetPreparationSourceName, failure.ErrorCode);
        Assert.Equal(nameof(GetDatasetPreparationBoardImageQuery.SourceName), failure.PropertyName);
    }

    [Theory]
    [InlineData(null)]
    [InlineData("")]
    [InlineData("   ")]
    public void Validate_ReturnsInvalidBoardFolderName_WhenBoardFolderNameIsMissing(string? boardFolderName)
    {
        var result = _validator.Validate(new GetDatasetPreparationBoardImageQuery(
            PreparationName: "preparation-001",
            SourceName: "v1_training",
            BoardFolderName: boardFolderName));

        var failure = Assert.Single(result.Errors);
        Assert.Equal(GetDatasetPreparationBoardImageErrorTypes.InvalidDatasetPreparationBoardFolderName, failure.ErrorCode);
        Assert.Equal(nameof(GetDatasetPreparationBoardImageQuery.BoardFolderName), failure.PropertyName);
    }

    [Theory]
    [InlineData("../Image1")]
    [InlineData("Image/1")]
    [InlineData("Image\\1")]
    [InlineData("Image:1")]
    public void Validate_ReturnsInvalidBoardFolderName_WhenBoardFolderNameContainsForbiddenCharacters(
        string boardFolderName)
    {
        var result = _validator.Validate(new GetDatasetPreparationBoardImageQuery(
            PreparationName: "preparation-001",
            SourceName: "v1_training",
            BoardFolderName: boardFolderName));

        var failure = Assert.Single(result.Errors);
        Assert.Equal(GetDatasetPreparationBoardImageErrorTypes.InvalidDatasetPreparationBoardFolderName, failure.ErrorCode);
        Assert.Equal(nameof(GetDatasetPreparationBoardImageQuery.BoardFolderName), failure.PropertyName);
    }
}
