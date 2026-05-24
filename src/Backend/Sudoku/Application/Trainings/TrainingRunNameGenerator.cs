using System.Text;

namespace Sudoku.Application.Trainings;

public sealed class TrainingRunNameGenerator : ITrainingRunNameGenerator
{
    private const int MaxSegmentLength = 32;

    public string Generate(
        DateTimeOffset createdAtUtc,
        string runNamePrefix,
        string baseModelName,
        string processedDatasetName,
        int attempt)
    {
        var timestamp = createdAtUtc.UtcDateTime.ToString("yyyyMMdd-HHmmss");
        var baseSegment = Slugify(baseModelName, MaxSegmentLength);
        var datasetSegment = Slugify(processedDatasetName, MaxSegmentLength);
        var candidate = $"{Slugify(runNamePrefix, 16)}-{timestamp}-{baseSegment}-{datasetSegment}";

        return attempt == 0
            ? candidate
            : $"{candidate}-{attempt}";
    }

    private static string Slugify(string value, int maxLength)
    {
        var builder = new StringBuilder(value.Length);
        foreach (var character in value.Trim())
        {
            if (char.IsLetterOrDigit(character))
            {
                builder.Append(char.ToLowerInvariant(character));
                continue;
            }

            if (character is '-' or '_')
            {
                builder.Append(character);
                continue;
            }

            if (builder.Length == 0 || builder[^1] != '-')
            {
                builder.Append('-');
            }
        }

        var slug = builder.ToString().Trim('-');
        if (string.IsNullOrWhiteSpace(slug))
        {
            slug = "run";
        }

        return slug.Length <= maxLength
            ? slug
            : slug[..maxLength].TrimEnd('-');
    }
}
