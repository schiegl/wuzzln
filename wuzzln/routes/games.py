import sqlite3
import time
from datetime import datetime

from litestar import get
from litestar.response import Template

from wuzzln.data import Game, get_season


class HistoryGame(Game):
    def pretty_date(self) -> str:
        dt = datetime.fromtimestamp(self.timestamp)
        return dt.strftime("%Y-%m-%d %H:%M")


@get("/games")
async def get_games_page(db: sqlite3.Connection) -> Template:
    season = get_season()
    query = "SELECT * FROM game WHERE season = ? ORDER BY timestamp DESC"
    games = [HistoryGame(*row) for row in db.execute(query, (season,))]
    player_name = dict(db.execute("SELECT id, name FROM player"))
    ten_min_ago = time.time() - 60 * 10

    return Template(
        "games.html",
        context={
            "games": games,
            "player_name": player_name,
            "delete_timestamp_threshold": ten_min_ago,
            "season": season,
        },
    )
