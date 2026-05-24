using Sudoku.Models.Sudoku;

namespace Sudoku.Application.SudokuSolve;

internal static class SudokuGridRules
{
    public static bool TryFindConflict(
        SudokuGrid grid,
        out string message)
    {
        for (var row = 0; row < 9; row++)
        {
            var duplicates = FindDuplicates(Enumerable.Range(0, 9)
                .Select(column => grid.GetDigit(new SudokuCellPosition(row, column))));
            if (duplicates.Count > 0)
            {
                message = $"Grid łamie reguły sudoku w wierszu {row + 1}.";
                return true;
            }
        }

        for (var column = 0; column < 9; column++)
        {
            var duplicates = FindDuplicates(Enumerable.Range(0, 9)
                .Select(row => grid.GetDigit(new SudokuCellPosition(row, column))));
            if (duplicates.Count > 0)
            {
                message = $"Grid łamie reguły sudoku w kolumnie {column + 1}.";
                return true;
            }
        }

        for (var blockRow = 0; blockRow < 3; blockRow++)
        {
            for (var blockColumn = 0; blockColumn < 3; blockColumn++)
            {
                var digits = new List<int?>(9);
                for (var row = blockRow * 3; row < (blockRow + 1) * 3; row++)
                {
                    for (var column = blockColumn * 3; column < (blockColumn + 1) * 3; column++)
                    {
                        digits.Add(grid.GetDigit(new SudokuCellPosition(row, column)));
                    }
                }

                var duplicates = FindDuplicates(digits);
                if (duplicates.Count > 0)
                {
                    message = $"Grid łamie reguły sudoku w bloku 3x3 ({blockRow + 1},{blockColumn + 1}).";
                    return true;
                }
            }
        }

        message = string.Empty;
        return false;
    }

    public static IReadOnlyList<int> GetAllowedDigits(
        SudokuGrid grid,
        SudokuCellPosition position)
    {
        if (!grid.IsEmpty(position))
        {
            return Array.Empty<int>();
        }

        var usedDigits = new HashSet<int>();

        for (var index = 0; index < 9; index++)
        {
            AddDigitIfPresent(grid.GetDigit(new SudokuCellPosition(position.Row, index)), usedDigits);
            AddDigitIfPresent(grid.GetDigit(new SudokuCellPosition(index, position.Column)), usedDigits);
        }

        var blockRowStart = (position.Row / 3) * 3;
        var blockColumnStart = (position.Column / 3) * 3;
        for (var row = blockRowStart; row < blockRowStart + 3; row++)
        {
            for (var column = blockColumnStart; column < blockColumnStart + 3; column++)
            {
                AddDigitIfPresent(grid.GetDigit(new SudokuCellPosition(row, column)), usedDigits);
            }
        }

        var candidates = new List<int>(9);
        for (var digit = 1; digit <= 9; digit++)
        {
            if (!usedDigits.Contains(digit))
            {
                candidates.Add(digit);
            }
        }

        return candidates;
    }

    private static HashSet<int> FindDuplicates(IEnumerable<int?> digits)
    {
        var seen = new HashSet<int>();
        var duplicates = new HashSet<int>();

        foreach (var digit in digits)
        {
            if (!digit.HasValue)
            {
                continue;
            }

            if (!seen.Add(digit.Value))
            {
                duplicates.Add(digit.Value);
            }
        }

        return duplicates;
    }

    private static void AddDigitIfPresent(int? digit, ISet<int> target)
    {
        if (digit.HasValue)
        {
            target.Add(digit.Value);
        }
    }
}
