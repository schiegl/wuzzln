from datetime import datetime, timedelta

import pytest

from wuzzln.data import get_season


@pytest.mark.parametrize(
    "timestamp,season",
    [
        ((2024, 1, 1), "2024-1"),
        ((2024, 3, 31), "2024-1"),
        ((2024, 4, 1), "2024-2"),
        ((2024, 6, 30), "2024-2"),
        ((2024, 8, 1), "2024-3"),
        ((2024, 9, 30), "2024-3"),
        ((2024, 10, 1), "2024-4"),
        ((2024, 12, 31), "2024-4"),
        ((2025, 1, 1), "2025-1"),
    ],
)
def test_get_season(timestamp, season):
    assert get_season(datetime(*timestamp)) == season


@pytest.mark.parametrize(
    "offset,season",
    [
        (-4, "2023-1"),
        (-3, "2023-2"),
        (-2, "2023-3"),
        (-1, "2023-4"),
        (0, "2024-1"),
        (1, "2024-2"),
        (2, "2024-3"),
        (3, "2024-4"),
        (4, "2025-1"),
    ],
)
def test_get_season_offset(offset, season):
    # iterate through all days of quarter
    dt = datetime(2024, 1, 1)
    while dt < datetime(2024, 4, 1):
        assert get_season(dt, offset) == season, dt
        dt += timedelta(days=1)
