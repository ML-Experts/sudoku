import json
import logging
from pathlib import Path

LOGGER = logging.getLogger(__name__)


class ReportCorruptedError(Exception):
    pass


class TrainingReportWriter:
    def write(
        self,
        report_directory_path: str,
        summary: dict,
        metrics: dict,
        history: list[dict] | None = None,
    ) -> dict[str, str | None]:
        report_directory = Path(report_directory_path)
        report_directory.mkdir(parents=True, exist_ok=True)

        summary_path = report_directory / "summary.json"
        metrics_path = report_directory / "metrics.json"
        confusion_matrix_path = report_directory / "confusion_matrix.json"
        metrics_summary = {
            "accuracy": metrics.get("accuracy"),
            "precisionMacro": metrics.get("precisionMacro"),
            "recallMacro": metrics.get("recallMacro"),
            "f1Macro": metrics.get("f1Macro"),
        }
        summary_payload = {
            **summary,
            "metricsSummary": metrics_summary,
        }
        metrics_payload = {
            "runName": summary.get("runName"),
            "accuracy": metrics.get("accuracy"),
            "precisionMacro": metrics.get("precisionMacro"),
            "recallMacro": metrics.get("recallMacro"),
            "f1Macro": metrics.get("f1Macro"),
            "classes": metrics.get("classes", metrics.get("perClass", [])),
            "history": history or [],
        }

        summary_path.write_text(
            json.dumps(summary_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        metrics_path.write_text(
            json.dumps(metrics_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        confusion_matrix_path.write_text(
            json.dumps(
                {
                    "classNames": metrics["classNames"],
                    "matrix": metrics["confusionMatrix"],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        self._validate_report_files(
            summary_path,
            metrics_path,
            confusion_matrix_path,
        )
        LOGGER.info(
            "Training reports written.",
            extra={
                "run_name": summary.get("runName"),
                "report_files": (
                    "summary.json",
                    "metrics.json",
                    "confusion_matrix.json",
                ),
            },
        )

        return {
            "summary": "summary.json",
            "metrics": "metrics.json",
            "confusionMatrix": "confusion_matrix.json",
        }

    def _validate_report_files(
        self,
        summary_path: Path,
        metrics_path: Path,
        confusion_matrix_path: Path,
    ) -> None:
        try:
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
            confusion_matrix = json.loads(
                confusion_matrix_path.read_text(encoding="utf-8")
            )
        except Exception as error:
            raise ReportCorruptedError("Training report JSON is invalid.") from error

        self._require_keys(
            summary,
            (
                "runName",
                "baseModelName",
                "processedDatasetName",
                "producedModelName",
                "architectureType",
                "trainingProfileName",
                "augmentationProfileName",
                "benchmarkName",
                "seed",
                "epochs",
                "metricsSummary",
            ),
        )
        self._require_keys(
            metrics,
            (
                "runName",
                "accuracy",
                "precisionMacro",
                "recallMacro",
                "f1Macro",
                "classes",
                "history",
            ),
        )
        self._require_keys(confusion_matrix, ("classNames", "matrix"))
        if not isinstance(metrics["history"], list):
            raise ReportCorruptedError("Training history must be a list.")
        if not isinstance(metrics["classes"], list):
            raise ReportCorruptedError("Per-class metrics must be a list.")
        if not isinstance(confusion_matrix["classNames"], list):
            raise ReportCorruptedError("Confusion matrix class names must be a list.")
        if not isinstance(confusion_matrix["matrix"], list):
            raise ReportCorruptedError("Confusion matrix must be a list.")

    def _require_keys(self, payload: dict, keys: tuple[str, ...]) -> None:
        missing_keys = [key for key in keys if key not in payload]
        if missing_keys:
            raise ReportCorruptedError(
                f"Training report is missing keys: {', '.join(missing_keys)}."
            )
