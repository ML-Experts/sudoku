from enum import StrEnum


class TrainingRunStage(StrEnum):
    QUEUED = "queued"
    TRAINING = "training"
    EVALUATION = "evaluation"
    FINISHED = "finished"
