using Microsoft.Extensions.Options;
using Sudoku.Application.Abstractions;
using Sudoku.Infrastructure.Configuration;

namespace Sudoku.Infrastructure.Ml;

public sealed class MlTrainingEventsPathProvider : ITrainingEventsPathProvider
{
    private readonly MlServiceOptions _options;

    public MlTrainingEventsPathProvider(IOptions<MlServiceOptions> options)
    {
        _options = options.Value;
    }

    public string GetEventsPath(string runName)
    {
        return _options.TrainingEventsPathTemplate.Replace(
            "{runName}",
            Uri.EscapeDataString(runName),
            StringComparison.Ordinal);
    }
}
