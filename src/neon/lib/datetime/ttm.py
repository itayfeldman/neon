import pandas as pd

from .day_count import DayCount


def time_to_maturity_ACT360(start_date: pd.Timestamp, end_date: pd.Timestamp) -> float:
    """Calculate time to maturity in years using ACT/360 convention."""
    return (end_date - start_date).days / 360


def time_to_maturity_ACT365(start_date: pd.Timestamp, end_date: pd.Timestamp) -> float:
    """Calculate time to maturity in years using ACT/365 convention."""
    return (end_date - start_date).days / 365


def time_to_maturity_THIRTY360(
    start_date: pd.Timestamp, end_date: pd.Timestamp
) -> float:
    """Calculate time to maturity in years using 30/360 convention."""
    y1, m1, d1 = start_date.year, start_date.month, start_date.day
    y2, m2, d2 = end_date.year, end_date.month, end_date.day
    d1 = min(d1, 30)
    if d1 == 30:
        d2 = min(d2, 30)
    days = 360 * (y2 - y1) + 30 * (m2 - m1) + (d2 - d1)
    return days / 360


day_count_functions = {
    DayCount.ACT360: time_to_maturity_ACT360,
    DayCount.ACT365: time_to_maturity_ACT365,
    DayCount.THIRTY360: time_to_maturity_THIRTY360,
}


def time_to_maturity(
    start_date: str, end_date: str, day_count: DayCount = DayCount.ACT365
) -> float:

    _start_date = pd.to_datetime(start_date)
    _end_date = pd.to_datetime(end_date)

    """Calculate the time to maturity in years under the given day count convention."""
    return day_count_functions[day_count](_start_date, _end_date)
