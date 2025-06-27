from enum import StrEnum


class TaskState(StrEnum):
    waiting = "waiting"
    infer = "infer"
    down = "down"
    canceled = "canceled"
