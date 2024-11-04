import sqlite3

from wuzzln.data import Game, Rating, get_season
from wuzzln.rating import compute_ratings


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


def _add_prev_season_ratings(db: sqlite3.Connection) -> None:
    all_seasons = [row[0] for row in db.execute("SELECT distinct season FROM game")]
    cur_season = get_season()
    qmarks = ",".join("?" for _ in Rating._fields)
    db.execute(f"CREATE TEMP TABLE rating({','.join(Rating._fields)})")
    for season in all_seasons:
        if season != cur_season:
            query = "SELECT * FROM game WHERE season = ? ORDER BY timestamp"
            games = tuple(Game(*row) for row in db.execute(query, (season,)))
            ratings = compute_ratings(games)
            db.executemany(f"INSERT INTO rating VALUES ({qmarks})", ratings)

    db.commit()


async def get_database() -> sqlite3.Connection:
    db = sqlite3.connect("database/db.sqlite", detect_types=1)
    _add_prev_season_ratings(db)
    return db
