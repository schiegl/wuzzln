import sqlite3
from collections import Counter

from cachetools import LRUCache, cached

from wuzzln.data import Game, PlayerId


def insert(db: sqlite3.Connection, value: Game):
    if isinstance(value, Game):
        fields = Game._fields
    else:
        raise NotImplementedError(f"Unsupported insert type: {type(value)}")

    qmarks = ",".join("?" for _ in fields)
    fields_str = ",".join(fields)
    table = type(value).__name__
    query = f"INSERT INTO {table}({fields_str}) VALUES ({qmarks})"

    db.execute(query, value)


def exists(db: sqlite3.Connection, table: str, column: str, value) -> bool:
    query = f"SELECT exists(SELECT * FROM {table} WHERE {column} == ?)"
    row = db.execute(query, (value,)).fetchone()
    return row[0] == 1


@cached(LRUCache(5), key=lambda _, timestamp: timestamp)
def query_game_count(db: sqlite3.Connection, timestamp: float) -> Counter[PlayerId]:
    """Get all games played before a timestamp.

    Cached because this is used on the front page

    :param db: game database
    :param timestamp: unix epoch timestamp
    :return: player id to game count
    """
    query = """
        SELECT p.id, count(*)
        FROM player AS p JOIN game AS g
            ON p.id IN (g.defense_a, g.offense_a, g.defense_b, g.offense_b)
        WHERE timestamp < ?
        GROUP BY p.id
    """
    return Counter(dict(db.execute(query, (timestamp,))))
