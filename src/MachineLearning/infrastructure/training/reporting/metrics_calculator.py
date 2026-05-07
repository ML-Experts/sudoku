import numpy as np
from numpy.typing import NDArray


class MetricsCalculator:
    def calculate(
        self,
        y_true: NDArray[np.int64],
        y_pred: NDArray[np.int64],
        class_names: tuple[str, ...],
    ) -> dict:
        class_count = len(class_names)
        confusion_matrix = np.zeros((class_count, class_count), dtype=np.int64)
        for true_label, predicted_label in zip(y_true, y_pred, strict=False):
            if 0 <= true_label < class_count and 0 <= predicted_label < class_count:
                confusion_matrix[int(true_label), int(predicted_label)] += 1

        total = int(confusion_matrix.sum())
        correct = int(np.trace(confusion_matrix))
        per_class = []
        precision_values = []
        recall_values = []
        f1_values = []

        for index, class_name in enumerate(class_names):
            true_positive = int(confusion_matrix[index, index])
            false_positive = int(confusion_matrix[:, index].sum()) - true_positive
            false_negative = int(confusion_matrix[index, :].sum()) - true_positive
            support = int(confusion_matrix[index, :].sum())
            precision = self._safe_divide(
                true_positive,
                true_positive + false_positive,
            )
            recall = self._safe_divide(
                true_positive,
                true_positive + false_negative,
            )
            f1 = self._safe_divide(2 * precision * recall, precision + recall)
            precision_values.append(precision)
            recall_values.append(recall)
            f1_values.append(f1)
            per_class.append(
                {
                    "label": class_name,
                    "precision": precision,
                    "recall": recall,
                    "f1": f1,
                    "support": support,
                }
            )

        return {
            "accuracy": self._safe_divide(correct, total),
            "precisionMacro": float(np.mean(precision_values)),
            "recallMacro": float(np.mean(recall_values)),
            "f1Macro": float(np.mean(f1_values)),
            "perClass": per_class,
            "classes": per_class,
            "confusionMatrix": confusion_matrix.tolist(),
            "classNames": list(class_names),
        }

    def _safe_divide(self, numerator: float, denominator: float) -> float:
        if denominator == 0:
            return 0.0
        return float(numerator / denominator)
