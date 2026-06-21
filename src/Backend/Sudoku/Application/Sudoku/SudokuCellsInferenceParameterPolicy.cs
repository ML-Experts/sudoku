using System.Globalization;

namespace Sudoku.Application.Sudoku;

public static class SudokuCellsInferenceParameterPolicy
{
    public static InferSudokuCellDigitMlResolvedConfigurationDto Resolve(
        InferSudokuCellDigitCommand command,
        SudokuCellsInferenceOptions options)
    {
        var resolvedConfiguration = new InferSudokuCellDigitMlResolvedConfigurationDto(
            InferenceProfileName: options.InferenceProfileName,
            EmptyCellInnerMarginRatio: command.EmptyCellInnerMarginRatio ?? options.EmptyCellInnerMarginRatio,
            EmptyCellDarkPixelRatioThreshold: command.EmptyCellDarkPixelRatioThreshold ?? options.EmptyCellDarkPixelRatioThreshold,
            CenterAreaRatio: command.CenterAreaRatio ?? options.CenterAreaRatio,
            MinComponentAreaRatio: command.MinComponentAreaRatio ?? options.MinComponentAreaRatio,
            LineArtifactMinSpanRatio: command.LineArtifactMinSpanRatio ?? options.LineArtifactMinSpanRatio,
            LineArtifactMaxThicknessRatio: command.LineArtifactMaxThicknessRatio ?? options.LineArtifactMaxThicknessRatio,
            EmptyCellMinSegmentLengthPx: command.EmptyCellMinSegmentLengthPx ?? options.EmptyCellMinSegmentLengthPx,
            EmptyCellFilteredSegmentCountThreshold: command.EmptyCellFilteredSegmentCountThreshold ?? options.EmptyCellFilteredSegmentCountThreshold);

        ValidateResolved(resolvedConfiguration);
        return resolvedConfiguration;
    }

    public static void ValidateResolved(InferSudokuCellDigitMlResolvedConfigurationDto configuration)
    {
        if (!IsInnerMarginRatioValid(configuration.EmptyCellInnerMarginRatio))
        {
            throw CreateInvalidResolvedConfigurationException(
                nameof(configuration.EmptyCellInnerMarginRatio),
                configuration.EmptyCellInnerMarginRatio,
                "wartość musi mieścić się w zakresie [0.0, 0.5).");
        }

        ValidateUnitRatio(
            nameof(configuration.EmptyCellDarkPixelRatioThreshold),
            configuration.EmptyCellDarkPixelRatioThreshold);
        ValidateUnitRatio(nameof(configuration.CenterAreaRatio), configuration.CenterAreaRatio);
        ValidateUnitRatio(nameof(configuration.MinComponentAreaRatio), configuration.MinComponentAreaRatio);
        ValidateUnitRatio(nameof(configuration.LineArtifactMinSpanRatio), configuration.LineArtifactMinSpanRatio);
        ValidateUnitRatio(nameof(configuration.LineArtifactMaxThicknessRatio), configuration.LineArtifactMaxThicknessRatio);

        if (!IsPositiveInt(configuration.EmptyCellMinSegmentLengthPx))
        {
            throw CreateInvalidResolvedConfigurationException(
                nameof(configuration.EmptyCellMinSegmentLengthPx),
                configuration.EmptyCellMinSegmentLengthPx,
                "wartość musi być większa od 0.");
        }

        if (!IsPositiveInt(configuration.EmptyCellFilteredSegmentCountThreshold))
        {
            throw CreateInvalidResolvedConfigurationException(
                nameof(configuration.EmptyCellFilteredSegmentCountThreshold),
                configuration.EmptyCellFilteredSegmentCountThreshold,
                "wartość musi być większa od 0.");
        }
    }

    public static bool IsInnerMarginRatioValid(double? value)
    {
        return value is null || (value.Value >= 0d && value.Value < 0.5d);
    }

    public static bool IsUnitRatioValid(double? value)
    {
        return value is null || (value.Value >= 0d && value.Value <= 1d);
    }

    public static bool IsPositiveInt(int? value)
    {
        return value is null || value.Value > 0;
    }

    private static void ValidateUnitRatio(string propertyName, double value)
    {
        if (!IsUnitRatioValid(value))
        {
            throw CreateInvalidResolvedConfigurationException(
                propertyName,
                value,
                "wartość musi mieścić się w zakresie [0.0, 1.0].");
        }
    }

    private static InvalidOperationException CreateInvalidResolvedConfigurationException(
        string propertyName,
        object value,
        string reason)
    {
        return new InvalidOperationException(
            $"Nieprawidłowa resolved konfiguracja Sudoku cells inference. Pole '{propertyName}' ma wartość '{Convert.ToString(value, CultureInfo.InvariantCulture)}', a {reason}");
    }
}
