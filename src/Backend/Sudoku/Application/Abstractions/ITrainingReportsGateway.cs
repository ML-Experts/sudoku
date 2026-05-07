using Sudoku.Application.Trainings;

namespace Sudoku.Application.Abstractions;

public interface ITrainingReportsGateway
{
    Task<TrainingRunReportDto> GetReportAsync(
        string runName,
        string summaryRelativePath,
        string metricsRelativePath,
        string confusionMatrixRelativePath,
        CancellationToken cancellationToken = default);
}
