from enum import Enum


class DatasetSourceType(str, Enum):
    BOARD = "board"
    DIGIT = "digit"
    BOARD_DERIVED = "boardDerived"
