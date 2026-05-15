using Sudoku.Application.SudokuSolve;
using Sudoku.Models.Sudoku;

namespace Application.Tests;

public sealed class SudokuBacktrackingSolverTests
{
    private readonly SudokuBacktrackingSolver _solver = new();

    [Fact]
    public async Task SolveAsync_ReturnsCompletedAndPreservesGivenDigits_ForSolvableGrid()
    {
        var inputGrid = new int?[][]
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
        };
        var expectedSolvedGrid = new int?[][]
        {
            new int?[] { 5, 3, 4, 6, 7, 8, 9, 1, 2 },
            new int?[] { 6, 7, 2, 1, 9, 5, 3, 4, 8 },
            new int?[] { 1, 9, 8, 3, 4, 2, 5, 6, 7 },
            new int?[] { 8, 5, 9, 7, 6, 1, 4, 2, 3 },
            new int?[] { 4, 2, 6, 8, 5, 3, 7, 9, 1 },
            new int?[] { 7, 1, 3, 9, 2, 4, 8, 5, 6 },
            new int?[] { 9, 6, 1, 5, 3, 7, 2, 8, 4 },
            new int?[] { 2, 8, 7, 4, 1, 9, 6, 3, 5 },
            new int?[] { 3, 4, 5, 2, 8, 6, 1, 7, 9 }
        };

        var grid = new SudokuGrid(inputGrid);
        var steps = new List<SudokuSolverStepDto>();

        var result = await _solver.SolveAsync(
            grid,
            (step, _) =>
            {
                steps.Add(step);
                return Task.CompletedTask;
            },
            CancellationToken.None);

        Assert.Equal(SudokuBacktrackingSolveResultDto.Completed, result.Outcome);
        Assert.NotEmpty(steps);
        AssertGridEqual(expectedSolvedGrid, grid.ToJaggedArray());

        for (var row = 0; row < 9; row++)
        {
            for (var column = 0; column < 9; column++)
            {
                if (inputGrid[row][column].HasValue)
                {
                    Assert.Equal(inputGrid[row][column], grid.ToJaggedArray()[row][column]);
                }
            }
        }
    }

    [Fact]
    public async Task SolveAsync_ReturnsUnsolvable_ForGridWithoutValidSolution()
    {
        var unsolvableGrid = new int?[][]
        {
            new int?[] { null, 3, 4, 6, 7, 5, 9, 1, 2 },
            new int?[] { 6, 7, 2, 1, 9, null, 3, 4, 8 },
            new int?[] { 1, 9, 8, 3, 4, 2, 5, 6, 7 },
            new int?[] { 8, 5, 9, 7, 6, 1, 4, 2, 3 },
            new int?[] { 4, 2, 6, 8, 5, 3, 7, 9, 1 },
            new int?[] { 7, 1, 3, 9, 2, 4, 8, 5, 6 },
            new int?[] { 9, 6, 1, 5, 3, 7, 2, 8, 4 },
            new int?[] { 2, 8, 7, 4, 1, 9, 6, 3, 5 },
            new int?[] { 3, 4, 5, 2, 8, 6, 1, 7, 9 }
        };

        var grid = new SudokuGrid(unsolvableGrid);

        var result = await _solver.SolveAsync(
            grid,
            (_, _) => Task.CompletedTask,
            CancellationToken.None);

        Assert.Equal(SudokuBacktrackingSolveResultDto.Unsolvable, result.Outcome);
    }

    private static void AssertGridEqual(int?[][] expected, int?[][] actual)
    {
        Assert.Equal(expected.Length, actual.Length);

        for (var row = 0; row < expected.Length; row++)
        {
            Assert.Equal(expected[row].Length, actual[row].Length);

            for (var column = 0; column < expected[row].Length; column++)
            {
                Assert.Equal(expected[row][column], actual[row][column]);
            }
        }
    }
}
