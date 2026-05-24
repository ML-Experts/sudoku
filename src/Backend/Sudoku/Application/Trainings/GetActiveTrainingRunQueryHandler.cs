using MediatR;
using Sudoku.Application.Abstractions;

namespace Sudoku.Application.Trainings;

public sealed class GetActiveTrainingRunQueryHandler
    : IRequestHandler<GetActiveTrainingRunQuery, GetActiveTrainingRunQueryResultDto>
{
    private static readonly HashSet<string> ActiveStatuses = new(StringComparer.OrdinalIgnoreCase)
    {
        "queued",
        "starting",
        "running",
        "cancelling"
    };

    private readonly ITrainingRunsGateway _trainingRunsGateway;

    public GetActiveTrainingRunQueryHandler(ITrainingRunsGateway trainingRunsGateway)
    {
        _trainingRunsGateway = trainingRunsGateway;
    }

    public async Task<GetActiveTrainingRunQueryResultDto> Handle(
        GetActiveTrainingRunQuery request,
        CancellationToken cancellationToken)
    {
        var runs = await _trainingRunsGateway.ListAsync(cancellationToken);
        var activeRuns = runs
            .Where(run => ActiveStatuses.Contains(run.Status))
            .OrderByDescending(run => run.CreatedAtUtc)
            .ToArray();

        if (activeRuns.Length == 0)
        {
            return new GetActiveTrainingRunQueryResultDto(
                HasActiveRun: false,
                Run: null);
        }

        if (activeRuns.Length > 1)
        {
            throw new InvalidOperationException(
                "Detected more than one active training run. This violates the single active run invariant.");
        }

        var activeRun = activeRuns[0];
        return new GetActiveTrainingRunQueryResultDto(
            HasActiveRun: true,
            Run: new ActiveTrainingRunDto(
                RunName: activeRun.RunName,
                Status: activeRun.Status,
                CreatedAtUtc: activeRun.CreatedAtUtc,
                BaseModelName: activeRun.BaseModelName,
                ProducedModelName: activeRun.ProducedModelName,
                ProcessedDatasetName: activeRun.ProcessedDatasetName,
                TrainingMode: activeRun.TrainingMode,
                TrainingProfileName: activeRun.TrainingProfileName,
                AugmentationProfileName: activeRun.AugmentationProfileName,
                BenchmarkName: activeRun.BenchmarkName,
                Seed: activeRun.Seed,
                EffectiveParameters: activeRun.EffectiveParameters,
                ProgressChannelUrl: activeRun.ProgressChannelUrl));
    }
}
