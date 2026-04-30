import json
from pathlib import Path


class TrainingReportWriter:
    def write(
        self,
        report_directory_path: str,
        summary: dict,
        metrics: dict,
    ) -> dict[str, str | None]:
        report_directory = Path(report_directory_path)
        report_directory.mkdir(parents=True, exist_ok=True)

        summary_path = report_directory / "summary.json"
        metrics_path = report_directory / "metrics.json"
        confusion_matrix_path = report_directory / "confusion_matrix.json"

        summary_path.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        metrics_path.write_text(
            json.dumps(metrics, ensure_ascii=False, indent=2),
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

        return {
            "summary": "summary.json",
            "metrics": "metrics.json",
            "confusionMatrix": "confusion_matrix.json",
        }
