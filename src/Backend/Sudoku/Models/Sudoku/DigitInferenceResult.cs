namespace Sudoku.Models.Sudoku;

public sealed class DigitInferenceResult
{
    public DigitInferenceResult(int? digit)
    {
        if (digit is < 1 or > 9)
        {
            throw new ArgumentOutOfRangeException(
                nameof(digit),
                "Rozpoznana cyfra musi być równa null albo mieścić się w zakresie 1..9.");
        }

        Digit = digit;
    }

    public int? Digit { get; }
}
