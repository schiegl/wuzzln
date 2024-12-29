from datetime import datetime, timedelta

from wuzzln.data import get_season


def is_season_start(now: datetime) -> bool:
    """Check if season start.

    :param now: current time
    :return: true if new season
    """
    now_season = get_season(now)
    week_ago_season = get_season(now - timedelta(days=14))
    return now_season != week_ago_season


def pretty_timestamp(timestamp: float, now: datetime | None = None) -> str:
    """Pretty format a timestamp.

    :param timestamp: unix epoch time
    :param now: timestamp relative to which format should appear.
    :return: string representation of timestamp
    """
    dt = datetime.fromtimestamp(timestamp)
    if now is None:
        return dt.strftime("%Y-%m-%d %H:%M")
    else:
        secs = (now - dt).total_seconds()
        if secs < 0 or secs > 3600 * 24 * 5:
            return dt.strftime("%Y-%m-%d %H:%M")

        # we're at most 5 days away
        if dt.day < now.day:
            return dt.strftime("%A %H:%M")

        # same day
        if secs >= 3600 * 24:
            total = secs // (3600 * 24)
            unit = "day"
        elif secs >= 3600:
            total = secs // 3600
            unit = "hour"
        elif secs >= 60:
            total = secs // 60
            unit = "minute"
        else:
            total = secs
            unit = "second"

        return f"{total:.0f} {unit}{'s' if total != 1 else ''} ago"
