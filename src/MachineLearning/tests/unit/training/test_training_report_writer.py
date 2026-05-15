import json
import tempfile
import unittest
from pathlib import Path

from infrastructure.training.reporting.training_report_writer import (
    TrainingReportWriter,
)


class TrainingReportWriterTests(unittest.TestCase):
    def test_write_should_create_uc09_report_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            report_directory = Path(temp_directory)
            writer = TrainingReportWriter()

            paths = writer.write(
                str(report_directory),
                {
                    "runName": "train-1",
                    "baseModelName": "cnn-bootstrap",
                    "processedDatasetName": "digits",
                    "producedModelName": "train-1",
                    "architectureType": "custom-cnn-v1",
                    "trainingProfileName": "cnn-default-v1",
                    "augmentationProfileName": "digits-light-v1",
                    "benchmarkName": "sudoku-benchmark-v1",
                    "seed": 1234,
                    "epochs": 3,
                    "device": "cpu",
                    "trainingDurationSeconds": 1.25,
                    "averageInferenceTimeMs": 0.5,
                },
                {
                    "accuracy": 0.9,
                    "precisionMacro": 0.8,
                    "recallMacro": 0.7,
                    "f1Macro": 0.75,
                    "classes": [
                        {
                            "label": "1",
                            "precision": 0.8,
                            "recall": 0.7,
                            "f1": 0.75,
                            "support": 10,
                        }
                    ],
                    "classNames": ["1"],
                    "confusionMatrix": [[10]],
                },
                [
                    {
                        "epoch": 1,
                        "trainLoss": 0.2,
                        "validationLoss": 0.3,
                        "trainAccuracy": 0.8,
                        "validationAccuracy": 0.7,
                    }
                ],
            )

            summary = json.loads(
                (report_directory / "summary.json").read_text(encoding="utf-8")
            )
            metrics = json.loads(
                (report_directory / "metrics.json").read_text(encoding="utf-8")
            )
            confusion_matrix = json.loads(
                (report_directory / "confusion_matrix.json").read_text(
                    encoding="utf-8"
                )
            )

        self.assertEqual(paths["summary"], "summary.json")
        self.assertEqual(summary["metricsSummary"]["accuracy"], 0.9)
        self.assertEqual(summary["trainingDurationSeconds"], 1.25)
        self.assertEqual(metrics["history"][0]["epoch"], 1)
        self.assertEqual(confusion_matrix["matrix"], [[10]])


if __name__ == "__main__":
    unittest.main()
