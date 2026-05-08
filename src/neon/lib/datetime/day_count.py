from enum import StrEnum, auto


class DayCount(StrEnum):
    ACT360 = auto()
    ACT365 = auto()
    THIRTY360 = auto()
    # Add more day count conventions as needed
