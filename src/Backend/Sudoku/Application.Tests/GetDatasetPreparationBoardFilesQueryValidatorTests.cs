using Sudoku.Application.Datasets;

namespace Application.Tests;

public sealed class GetDatasetPreparationBoardFilesQueryValidatorTests
{
    private readonly GetDatasetPreparationBoardFilesQueryValidator _validator = new();

    [Fact]
    public void Validate_ReturnsNoErrors_ForValidRequest()
    {
        var result = _validator.Validate(new GetDatasetPreparationBoardFilesQuery(
            PreparationName: "preparation-001",
            SourceName: "v1_training",
            Page: 1,
            PageSize: 50));

        Assert.True(result.IsValid);
    }

    [Theory]
    [InlineData(null)]
    [InlineData("")]
    [InlineData("   ")]
    public void Validate_ReturnsInvalidPreparationName_WhenPreparationNameIsMissing(string? preparationName)
    {
        var result = _validator.Validate(new GetDatasetPreparationBoardFilesQuery(
            PreparationName: preparationName,
            SourceName: "v1_training",
            Page: 1,
            PageSize: 50));

        var failure = Assert.Single(result.Errors);
        Assert.Equal(GetDatasetPreparationBoardFilesErrorTypes.InvalidDatasetPreparationName, failure.ErrorCode);
        Assert.Equal(nameof(GetDatasetPreparationBoardFilesQuery.PreparationName), failure.PropertyName);
    }

    [Theory]
    [InlineData("../prep")]
    [InlineData("prep/name")]
    [InlineData("prep\\name")]
    [InlineData("prep:name")]
    public void Validate_ReturnsInvalidPreparationName_WhenPreparationNameContainsForbiddenCharacters(
        string preparationName)
    {
        var result = _validator.Validate(new GetDatasetPreparationBoardFilesQuery(
            PreparationName: preparationName,
            SourceName: "v1_training",
            Page: 1,
            PageSize: 50));

        var failure = Assert.Single(result.Errors);
        Assert.Equal(GetDatasetPreparationBoardFilesErrorTypes.InvalidDatasetPreparationName, failure.ErrorCode);
        Assert.Equal(nameof(GetDatasetPreparationBoardFilesQuery.PreparationName), failure.PropertyName);
    }

    [Theory]
    [InlineData(null)]
    [InlineData("")]
    [InlineData("   ")]
    public void Validate_ReturnsInvalidSourceName_WhenSourceNameIsMissing(string? sourceName)
    {
        var result = _validator.Validate(new GetDatasetPreparationBoardFilesQuery(
            PreparationName: "preparation-001",
            SourceName: sourceName,
            Page: 1,
            PageSize: 50));

        var failure = Assert.Single(result.Errors);
        Assert.Equal(GetDatasetPreparationBoardFilesErrorTypes.InvalidDatasetPreparationSourceName, failure.ErrorCode);
        Assert.Equal(nameof(GetDatasetPreparationBoardFilesQuery.SourceName), failure.PropertyName);
    }

    [Theory]
    [InlineData("../source")]
    [InlineData("source/name")]
    [InlineData("source\\name")]
    [InlineData("source:name")]
    public void Validate_ReturnsInvalidSourceName_WhenSourceNameContainsForbiddenCharacters(
        string sourceName)
    {
        var result = _validator.Validate(new GetDatasetPreparationBoardFilesQuery(
            PreparationName: "preparation-001",
            SourceName: sourceName,
            Page: 1,
            PageSize: 50));

        var failure = Assert.Single(result.Errors);
        Assert.Equal(GetDatasetPreparationBoardFilesErrorTypes.InvalidDatasetPreparationSourceName, failure.ErrorCode);
        Assert.Equal(nameof(GetDatasetPreparationBoardFilesQuery.SourceName), failure.PropertyName);
    }

    [Theory]
    [InlineData(null)]
    [InlineData(0)]
    [InlineData(-1)]
    public void Validate_ReturnsInvalidPage_WhenPageIsMissingOrLessThanOne(int? page)
    {
        var result = _validator.Validate(new GetDatasetPreparationBoardFilesQuery(
            PreparationName: "preparation-001",
            SourceName: "v1_training",
            Page: page,
            PageSize: 50));

        var failure = Assert.Single(result.Errors);
        Assert.Equal(GetDatasetPreparationBoardFilesErrorTypes.InvalidDatasetPreparationBoardFilesPage, failure.ErrorCode);
        Assert.Equal(nameof(GetDatasetPreparationBoardFilesQuery.Page), failure.PropertyName);
    }

    [Theory]
    [InlineData(null)]
    [InlineData(0)]
    [InlineData(-1)]
    [InlineData(201)]
    public void Validate_ReturnsInvalidPageSize_WhenPageSizeIsOutsideAllowedRange(int? pageSize)
    {
        var result = _validator.Validate(new GetDatasetPreparationBoardFilesQuery(
            PreparationName: "preparation-001",
            SourceName: "v1_training",
            Page: 1,
            PageSize: pageSize));

        var failure = Assert.Single(result.Errors);
        Assert.Equal(GetDatasetPreparationBoardFilesErrorTypes.InvalidDatasetPreparationBoardFilesPageSize, failure.ErrorCode);
        Assert.Equal(nameof(GetDatasetPreparationBoardFilesQuery.PageSize), failure.PropertyName);
    }
}
