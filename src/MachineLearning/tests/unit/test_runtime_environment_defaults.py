import os
import unittest
from unittest.mock import patch

from api.config.environment import get_preprocessing_settings


class RuntimeEnvironmentDefaultsTests(unittest.TestCase):
    def test_preprocessing_defaults_should_match_notebook_pipeline(self) -> None:
        tracked_keys = {
            "ML_PREPROCESS_BOARD_OUTPUT_SIZE",
            "ML_PREPROCESS_BOARD_EDGE_HOUGH_THRESHOLD",
            "ML_PREPROCESS_BOARD_EDGE_MIN_LINE_LENGTH_RATIO",
            "ML_PREPROCESS_BOARD_EDGE_MAX_LINE_GAP_RATIO",
        }
        preserved_env = {
            key: value for key, value in os.environ.items() if key not in tracked_keys
        }

        with patch.dict(os.environ, preserved_env, clear=True):
            settings = get_preprocessing_settings()

        self.assertEqual(settings.board_output_size, 720)
        self.assertEqual(settings.board_edge_hough_threshold, 35)
        self.assertEqual(settings.board_edge_min_line_length_ratio, 0.08)
        self.assertEqual(settings.board_edge_max_line_gap_ratio, 0.005)


if __name__ == "__main__":
    unittest.main()
