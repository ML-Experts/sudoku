using System.Text.Json;
using Sudoku.Application.SudokuSolve;

namespace Application.Tests;

public sealed class StartSudokuSolveCommandValidatorTests
{
    private readonly StartSudokuSolveCommandValidator _validator = new();

    [Fact]
    public void Validate_ReturnsNoErrors_ForValidGrid()
    {
        var command = new StartSudokuSolveCommand(ToJsonElement(new int?[][]
        {
            new int?[] { 5, 3, null, null, 7, null, null, null, null },
            new int?[] { 6, null, null, 1, 9, 5, null, null, null },
            new int?[] { null, 9, 8, null, null, null, null, 6, null },
            new int?[] { 8, null, null, null, 6, null, null, null, 3 },
            new int?[] { 4, null, null, 8, null, 3, null, null, 1 },
            new int?[] { 7, null, null, null, 2, null, null, null, 6 },
            new int?[] { null, 6, null, null, null, null, 2, 8, null },
            new int?[] { null, null, null, 4, 1, 9, null, null, 5 },
            new int?[] { null, null, null, null, 8, null, null, 7, 9 }
        }), 120);

        var result = _validator.Validate(command);

        Assert.True(result.IsValid);
    }

    [Fact]
    public void Validate_ReturnsInvalidRequest_WhenGridIsMissing()
    {
        var result = _validator.Validate(new StartSudokuSolveCommand(null, null));

        var failure = Assert.Single(result.Errors);
        Assert.Equal(SolveSudokuErrorTypes.InvalidRequest, failure.ErrorCode);
    }

    [Fact]
    public void Validate_ReturnsGridShapeInvalid_WhenGridHasWrongRowCount()
    {
        var result = _validator.Validate(new StartSudokuSolveCommand(ToJsonElement(new int?[][]
        {
            new int?[] { 1, 2, 3 }
        }), null));

        var failure = Assert.Single(result.Errors);
        Assert.Equal(SolveSudokuErrorTypes.GridShapeInvalid, failure.ErrorCode);
    }

    [Fact]
    public void Validate_ReturnsGridValueOutOfRange_WhenCellContainsInvalidValue()
    {
        var result = _validator.Validate(new StartSudokuSolveCommand(ToJsonElement(new object?[][]
        {
            new object?[] { 5, 3, null, null, 7, null, null, null, null },
            new object?[] { 6, null, null, 1, 9, 5, null, null, null },
            new object?[] { null, 9, 8, null, null, null, null, 6, null },
            new object?[] { 8, null, null, null, 6, null, null, null, 3 },
            new object?[] { 4, null, null, 8, null, 3, null, null, 1 },
            new object?[] { 7, null, null, null, 2, null, null, null, 6 },
            new object?[] { null, 6, null, null, null, null, 2, 8, null },
            new object?[] { null, null, null, 4, 1, 9, null, null, 5 },
            new object?[] { null, null, null, null, 8, null, null, 7, "x" }
        }), null));

        var failure = Assert.Single(result.Errors);
        Assert.Equal(SolveSudokuErrorTypes.GridValueOutOfRange, failure.ErrorCode);
    }

    [Fact]
    public void Validate_ReturnsNoErrors_WhenSolverStepDelayIsOutOfRange()
    {
        var command = new StartSudokuSolveCommand(
            ToJsonElement(new int?[][]
            {
                new int?[] { 5, 3, null, null, 7, null, null, null, null },
                new int?[] { 6, null, null, 1, 9, 5, null, null, null },
                new int?[] { null, 9, 8, null, null, null, null, 6, null },
                new int?[] { 8, null, null, null, 6, null, null, null, 3 },
                new int?[] { 4, null, null, 8, null, 3, null, null, 1 },
                new int?[] { 7, null, null, null, 2, null, null, null, 6 },
                new int?[] { null, 6, null, null, null, null, 2, 8, null },
                new int?[] { null, null, null, 4, 1, 9, null, null, 5 },
                new int?[] { null, null, null, null, 8, null, null, 7, 9 }
            }),
            -1);

        var result = _validator.Validate(command);

        Assert.True(result.IsValid);
    }

    private static JsonElement ToJsonElement<T>(T value)
    {
        return JsonSerializer.SerializeToElement(value);
    }
}
