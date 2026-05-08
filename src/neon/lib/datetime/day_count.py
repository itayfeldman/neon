from enum import StrEnum, auto


class DayCount(StrEnum):
    ACT360 = auto()
    ACT365 = auto()
    THIRTY360 = auto()
    ACTACT_ISDA = auto()
