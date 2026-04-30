using MediatR;

namespace Sudoku.Application.Trainings;

public sealed record GetTrainingRunRealtimeSnapshotQuery(
    string? RunName) : IRequest<GetTrainingRunRealtimeSnapshotResultDto>;
