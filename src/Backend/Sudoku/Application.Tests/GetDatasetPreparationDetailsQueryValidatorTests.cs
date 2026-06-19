using Sudoku.Application.Datasets;

namespace Application.Tests;

public sealed class GetDatasetPreparationDetailsQueryValidatorTests
{
    private readonly GetDatasetPreparationDetailsQueryValidator _validator = new();

    [Fact]
    public void Validate_ReturnsNoErrors_ForValidPreparationName()
    {
        var result = _validator.Validate(new GetDatasetPreparationDetailsQuery("preparation-001"));

        Assert.True(result.IsValid);
    }

    [Theory]
    [InlineData(null)]
    [InlineData("")]
    [InlineData("   ")]
    public void Validate_ReturnsInvalidPreparationName_WhenPreparationNameIsMissing(string? preparationName)
    {
        var result = _validator.Validate(new GetDatasetPreparationDetailsQuery(preparationName));

        var failure = Assert.Single(result.Errors);
        Assert.Equal(GetDatasetPreparationDetailsErrorTypes.InvalidDatasetPreparationName, failure.ErrorCode);
        Assert.Equal(nameof(GetDatasetPreparationDetailsQuery.PreparationName), failure.PropertyName);
    }

    [Theory]
    [InlineData("../prep")]
    [InlineData("prep/name")]
    [InlineData("prep\\name")]
    [InlineData("prep:name")]
    public void Validate_ReturnsInvalidPreparationName_WhenPreparationNameContainsForbiddenCharacters(
        string preparationName)
    {
        var result = _validator.Validate(new GetDatasetPreparationDetailsQuery(preparationName));

        var failure = Assert.Single(result.Errors);
        Assert.Equal(GetDatasetPreparationDetailsErrorTypes.InvalidDatasetPreparationName, failure.ErrorCode);
        Assert.Equal(nameof(GetDatasetPreparationDetailsQuery.PreparationName), failure.PropertyName);
    }
}
