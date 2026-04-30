namespace Sudoku.Application.Trainings;

public sealed record RecordTrainingRunEventResultDto(
    bool Accepted,
    string RunName,
    string Status,
    long? LastAcceptedSequence,
    string Disposition);
