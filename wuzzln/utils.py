from datetime import datetime


def pretty_timestamp(timestamp: float) -> str:
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime("%Y-%m-%d %H:%M")
