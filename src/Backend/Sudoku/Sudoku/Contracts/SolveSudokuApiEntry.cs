using System.Text.Json;

namespace Sudoku.Contracts;

public sealed record SolveSudokuApiEntry(
    JsonElement? Grid,
    int? SolverStepDelayMs);
