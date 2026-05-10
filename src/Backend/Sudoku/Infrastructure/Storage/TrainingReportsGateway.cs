using System.Text.Json;
using Microsoft.Extensions.Options;
using Sudoku.Application.Abstractions;
using Sudoku.Application.Storage;
using Sudoku.Application.Trainings;

namespace Sudoku.Infrastructure.Storage;

public sealed class TrainingReportsGateway : ITrainingReportsGateway
{
    private readonly IFileStorageGateway _fileStorageGateway;
    private readonly TrainingsStorageOptions _trainingsStorageOptions;

    public TrainingReportsGateway(
        IFileStorageGateway fileStorageGateway,
        IOptions<TrainingsStorageOptions> trainingsStorageOptions)
    {
        _fileStorageGateway = fileStorageGateway;
        _trainingsStorageOptions = trainingsStorageOptions.Value;
    }

    public async Task<TrainingRunReportDto> GetReportAsync(
        string runName,
        string summaryRelativePath,
        string metricsRelativePath,
        string confusionMatrixRelativePath,
        CancellationToken cancellationToken = default)
    {
        var reportDirectoryPath = Path.GetFullPath(Path.Combine(
            _trainingsStorageOptions.ReportsDirectoryPath,
            runName));

        using var summaryDocument = await ReadJsonAsync(
            reportDirectoryPath,
            summaryRelativePath,
            cancellationToken);
        using var metricsDocument = await ReadJsonAsync(
            reportDirectoryPath,
            metricsRelativePath,
            cancellationToken);
        using var confusionMatrixDocument = await ReadJsonAsync(
            reportDirectoryPath,
            confusionMatrixRelativePath,
            cancellationToken);

        return new TrainingRunReportDto(
            Status: "ready",
            Summary: ReadSummary(summaryDocument.RootElement),
            PerClassMetrics: ReadClassMetrics(metricsDocument.RootElement),
            History: ReadHistory(metricsDocument.RootElement),
            ConfusionMatrix: ReadConfusionMatrix(confusionMatrixDocument.RootElement));
    }

    private async Task<JsonDocument> ReadJsonAsync(
        string reportDirectoryPath,
        string relativePath,
        CancellationToken cancellationToken)
    {
        await using var stream = await _fileStorageGateway.OpenReadAsync(
            reportDirectoryPath,
            relativePath,
            cancellationToken);

        try
        {
            return await JsonDocument.ParseAsync(stream, cancellationToken: cancellationToken);
        }
        catch (JsonException exception)
        {
            throw new InvalidDataException("Plik raportu treningowego nie jest poprawnym JSON.", exception);
        }
    }

    private static TrainingReportSummaryDto ReadSummary(JsonElement root)
    {
        var metricsSummary = GetRequiredObject(root, "metricsSummary");

        return new TrainingReportSummaryDto(
            Accuracy: GetRequiredDecimal(metricsSummary, "accuracy"),
            PrecisionMacro: GetRequiredDecimal(metricsSummary, "precisionMacro"),
            RecallMacro: GetRequiredDecimal(metricsSummary, "recallMacro"),
            F1Macro: GetRequiredDecimal(metricsSummary, "f1Macro"),
            TrainingDurationSeconds: GetNullableDecimal(root, "trainingDurationSeconds"),
            AverageInferenceTimeMs: GetNullableDecimal(root, "averageInferenceTimeMs"));
    }

    private static IReadOnlyList<TrainingClassMetricDto> ReadClassMetrics(JsonElement root)
    {
        var classes = GetRequiredArray(root, "classes");
        var result = new List<TrainingClassMetricDto>();

        foreach (var item in classes.EnumerateArray())
        {
            result.Add(new TrainingClassMetricDto(
                Label: GetRequiredString(item, "label"),
                Precision: GetRequiredDecimal(item, "precision"),
                Recall: GetRequiredDecimal(item, "recall"),
                F1: GetRequiredDecimal(item, "f1"),
                Support: GetRequiredInt(item, "support")));
        }

        return result;
    }

    private static IReadOnlyList<TrainingMetricHistoryPointDto> ReadHistory(JsonElement root)
    {
        var history = GetRequiredArray(root, "history");
        var result = new List<TrainingMetricHistoryPointDto>();

        foreach (var item in history.EnumerateArray())
        {
            var epoch = GetRequiredInt(item, "epoch");
            if (epoch <= 0)
            {
                throw new InvalidDataException("Historia metryk zawiera niepoprawny numer epoki.");
            }

            result.Add(new TrainingMetricHistoryPointDto(
                Epoch: epoch,
                TrainLoss: GetNullableDecimal(item, "trainLoss"),
                ValidationLoss: GetNullableDecimal(item, "validationLoss"),
                TrainAccuracy: GetNullableDecimal(item, "trainAccuracy"),
                ValidationAccuracy: GetNullableDecimal(item, "validationAccuracy")));
        }

        return result;
    }

    private static TrainingConfusionMatrixDto ReadConfusionMatrix(JsonElement root)
    {
        var classNames = GetRequiredArray(root, "classNames")
            .EnumerateArray()
            .Select(item =>
            {
                if (item.ValueKind != JsonValueKind.String || string.IsNullOrWhiteSpace(item.GetString()))
                {
                    throw new InvalidDataException("confusionMatrix.classNames musi zawierać niepuste teksty.");
                }

                return item.GetString()!;
            })
            .ToArray();

        var matrixRows = GetRequiredArray(root, "matrix");
        var matrix = new List<IReadOnlyList<int>>();
        int? expectedColumnCount = null;

        foreach (var row in matrixRows.EnumerateArray())
        {
            if (row.ValueKind != JsonValueKind.Array)
            {
                throw new InvalidDataException("confusionMatrix.matrix musi być tablicą tablic.");
            }

            var values = row.EnumerateArray()
                .Select(item =>
                {
                    if (item.ValueKind != JsonValueKind.Number || !item.TryGetInt32(out var value) || value < 0)
                    {
                        throw new InvalidDataException("confusionMatrix.matrix musi zawierać nieujemne liczby całkowite.");
                    }

                    return value;
                })
                .ToArray();

            expectedColumnCount ??= values.Length;
            if (values.Length != expectedColumnCount.Value)
            {
                throw new InvalidDataException("confusionMatrix.matrix musi być macierzą prostokątną.");
            }

            matrix.Add(values);
        }

        if (classNames.Length != matrix.Count)
        {
            throw new InvalidDataException(
                "Liczba etykiet confusionMatrix.classNames musi odpowiadać liczbie wierszy macierzy.");
        }

        return new TrainingConfusionMatrixDto(
            ClassNames: classNames,
            Matrix: matrix);
    }

    private static JsonElement GetRequiredObject(JsonElement root, string propertyName)
    {
        if (!root.TryGetProperty(propertyName, out var property) || property.ValueKind != JsonValueKind.Object)
        {
            throw new InvalidDataException($"Raport treningowy nie zawiera obiektu {propertyName}.");
        }

        return property;
    }

    private static JsonElement GetRequiredArray(JsonElement root, string propertyName)
    {
        if (!root.TryGetProperty(propertyName, out var property) || property.ValueKind != JsonValueKind.Array)
        {
            throw new InvalidDataException($"Raport treningowy nie zawiera tablicy {propertyName}.");
        }

        return property;
    }

    private static string GetRequiredString(JsonElement root, string propertyName)
    {
        if (!root.TryGetProperty(propertyName, out var property)
            || property.ValueKind != JsonValueKind.String
            || string.IsNullOrWhiteSpace(property.GetString()))
        {
            throw new InvalidDataException($"Raport treningowy nie zawiera tekstowego pola {propertyName}.");
        }

        return property.GetString()!;
    }

    private static int GetRequiredInt(JsonElement root, string propertyName)
    {
        if (!root.TryGetProperty(propertyName, out var property)
            || property.ValueKind != JsonValueKind.Number
            || !property.TryGetInt32(out var value))
        {
            throw new InvalidDataException($"Raport treningowy nie zawiera całkowitego pola {propertyName}.");
        }

        return value;
    }

    private static decimal GetRequiredDecimal(JsonElement root, string propertyName)
    {
        if (!root.TryGetProperty(propertyName, out var property)
            || property.ValueKind != JsonValueKind.Number
            || !property.TryGetDecimal(out var value))
        {
            throw new InvalidDataException($"Raport treningowy nie zawiera liczbowego pola {propertyName}.");
        }

        return value;
    }

    private static decimal? GetNullableDecimal(JsonElement root, string propertyName)
    {
        if (!root.TryGetProperty(propertyName, out var property) || property.ValueKind == JsonValueKind.Null)
        {
            return null;
        }

        if (property.ValueKind != JsonValueKind.Number || !property.TryGetDecimal(out var value))
        {
            throw new InvalidDataException($"Pole {propertyName} musi być liczbą albo null.");
        }

        return value;
    }
}
