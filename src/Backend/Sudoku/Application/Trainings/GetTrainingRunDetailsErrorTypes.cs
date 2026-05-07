namespace Sudoku.Application.Trainings;

public static class GetTrainingRunDetailsErrorTypes
{
    public const string InvalidTrainingRunName = "invalid_training_run_name";
    public const string TrainingRunNotFound = "training_run_not_found";
    public const string TrainingRunDetailsConflict = "training_run_details_conflict";
    public const string TrainingRunReportInvalid = "training_run_report_invalid";
    public const string TrainingRunDetailsReadFailed = "training_run_details_read_failed";
}
