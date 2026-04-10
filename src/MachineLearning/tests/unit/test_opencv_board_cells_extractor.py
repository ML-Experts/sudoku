import unittest

import numpy as np

from infrastructure.vision.opencv_board_cells_extractor import (
    OpenCvBoardCellsExtractor,
)


class OpenCvBoardCellsExtractorTests(unittest.TestCase):
    def test_extract_should_split_board_into_expected_grid(self) -> None:
        board_image = np.zeros((90, 90), dtype=np.uint8)
        for row_index in range(9):
            for col_index in range(9):
                value = row_index * 9 + col_index
                row_slice = slice(row_index * 10, (row_index + 1) * 10)
                col_slice = slice(col_index * 10, (col_index + 1) * 10)
                board_image[row_slice, col_slice] = value

        extractor = OpenCvBoardCellsExtractor(
            grid_rows=9,
            grid_cols=9,
            cell_inner_margin_ratio=0.0,
            minimum_cell_size_px=5,
            output_cell_size_px=None,
        )

        result = extractor.extract(board_image)

        self.assertEqual(result.rows, 9)
        self.assertEqual(result.cols, 9)
        self.assertEqual(int(np.mean(result.cells[0][0])), 0)
        self.assertEqual(int(np.mean(result.cells[8][8])), 80)

    def test_extract_should_crop_cell_borders_with_margin(self) -> None:
        board_image = np.zeros((20, 20), dtype=np.uint8)
        board_image[0:4, :] = 255
        board_image[-4:, :] = 255
        board_image[:, 0:4] = 255
        board_image[:, -4:] = 255

        no_margin_extractor = OpenCvBoardCellsExtractor(
            grid_rows=1,
            grid_cols=1,
            cell_inner_margin_ratio=0.0,
            minimum_cell_size_px=6,
            output_cell_size_px=None,
        )
        with_margin_extractor = OpenCvBoardCellsExtractor(
            grid_rows=1,
            grid_cols=1,
            cell_inner_margin_ratio=0.25,
            minimum_cell_size_px=6,
            output_cell_size_px=None,
        )

        no_margin_result = no_margin_extractor.extract(board_image)
        with_margin_result = with_margin_extractor.extract(board_image)

        self.assertEqual(int(np.max(no_margin_result.cells[0][0])), 255)
        self.assertEqual(int(np.max(with_margin_result.cells[0][0])), 0)


if __name__ == "__main__":
    unittest.main()
