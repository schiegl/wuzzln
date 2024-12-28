import sqlite3
from datetime import datetime, timedelta

from litestar import get
from litestar.response import Template

from wuzzln.data import Game, get_season


@get("/games")
async def get_games_page(db: sqlite3.Connection, now: datetime) -> Template:
    season = get_season(now)
    query = "SELECT * FROM game WHERE season = ? ORDER BY timestamp DESC"
    games = [Game(*row) for row in db.execute(query, (season,))]
    player_name = dict(db.execute("SELECT id, name FROM player"))
    ten_min_ago = (now - timedelta(minutes=10)).timestamp()

    return Template(
        "games.html",
        context={
            "games": games,
            "player_name": player_name,
            "delete_timestamp_threshold": ten_min_ago,
            "season": season,
            "now": now,
        },
    )
