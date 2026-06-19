using Sudoku.Application.Datasets;

namespace Application.Tests;

public sealed class GetDatasetPreparationFoldersQueryValidatorTests
{
    private readonly GetDatasetPreparationFoldersQueryValidator _validator = new();

    [Theory]
    [InlineData("board")]
    [InlineData("digit")]
    public void Validate_ReturnsNoErrors_ForSupportedType(string type)
    {
        var result = _validator.Validate(new GetDatasetPreparationFoldersQuery("preparation-001", type));

        Assert.True(result.IsValid);
    }

    [Theory]
    [InlineData(null)]
    [InlineData("")]
    [InlineData("   ")]
    public void Validate_ReturnsInvalidPreparationName_WhenPreparationNameIsMissing(string? preparationName)
    {
        var result = _validator.Validate(new GetDatasetPreparationFoldersQuery(preparationName, "board"));

        var failure = Assert.Single(result.Errors);
        Assert.Equal(GetDatasetPreparationFoldersErrorTypes.InvalidDatasetPreparationName, failure.ErrorCode);
        Assert.Equal(nameof(GetDatasetPreparationFoldersQuery.PreparationName), failure.PropertyName);
    }

    [Theory]
    [InlineData("../prep")]
    [InlineData("prep/name")]
    [InlineData("prep\\name")]
    [InlineData("prep:name")]
    public void Validate_ReturnsInvalidPreparationName_WhenPreparationNameContainsForbiddenCharacters(
        string preparationName)
    {
        var result = _validator.Validate(new GetDatasetPreparationFoldersQuery(preparationName, "board"));

        var failure = Assert.Single(result.Errors);
        Assert.Equal(GetDatasetPreparationFoldersErrorTypes.InvalidDatasetPreparationName, failure.ErrorCode);
        Assert.Equal(nameof(GetDatasetPreparationFoldersQuery.PreparationName), failure.PropertyName);
    }

    [Theory]
    [InlineData(null)]
    [InlineData("")]
    [InlineData("   ")]
    public void Validate_ReturnsInvalidType_WhenTypeIsMissing(string? type)
    {
        var result = _validator.Validate(new GetDatasetPreparationFoldersQuery("preparation-001", type));

        var failure = Assert.Single(result.Errors);
        Assert.Equal(GetDatasetPreparationFoldersErrorTypes.InvalidDatasetPreparationType, failure.ErrorCode);
        Assert.Equal(nameof(GetDatasetPreparationFoldersQuery.Type), failure.PropertyName);
    }

    [Theory]
    [InlineData("cells")]
    [InlineData("raw")]
    public void Validate_ReturnsInvalidType_WhenTypeIsUnsupported(string type)
    {
        var result = _validator.Validate(new GetDatasetPreparationFoldersQuery("preparation-001", type));

        var failure = Assert.Single(result.Errors);
        Assert.Equal(GetDatasetPreparationFoldersErrorTypes.InvalidDatasetPreparationType, failure.ErrorCode);
        Assert.Equal(nameof(GetDatasetPreparationFoldersQuery.Type), failure.PropertyName);
    }
}
