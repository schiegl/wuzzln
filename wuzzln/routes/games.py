import sqlite3
from datetime import datetime, timedelta

from litestar import Request, get
from litestar.datastructures import Cookie
from litestar.response import Template

from wuzzln.data import Game, get_season


@get("/games")
async def get_games_page(request: Request, db: sqlite3.Connection, now: datetime) -> Template:
    season = get_season(now)
    query = "SELECT * FROM game WHERE timestamp < ? AND season = ? ORDER BY timestamp DESC"
    games = [Game(*row) for row in db.execute(query, (now.timestamp(), season))]
    player_name = dict(db.execute("SELECT id, name FROM player"))
    ten_min_ago = (now - timedelta(minutes=10)).timestamp()

    try:
        last_visit = float(request.cookies.get("wuzzln-games-last-check"))  # type: ignore
    except TypeError:
        last_visit = games[-1].timestamp - 1 if games else now.timestamp()

    return Template(
        "games.html",
        context={
            "games": games,
            "player_name": player_name,
            "season": season,
            "show_delete_timestamp": ten_min_ago,
            "show_new_game_timestamp": last_visit,
        },
        cookies=[
            Cookie(
                "wuzzln-games-last-check",
                value=str(now.timestamp()),
                secure=True,
                max_age=3600 * 24 * 90,
            )
        ],
    )
