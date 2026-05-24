namespace Sudoku.Contracts;

public sealed record TrainingRunEventAckApiResponse(
    bool Accepted,
    string RunName,
    string Status,
    long? LastAcceptedSequence,
    string Disposition);
