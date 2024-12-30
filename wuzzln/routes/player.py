import sqlite3
from datetime import datetime

from litestar import get
from litestar.exceptions import NotFoundException
from litestar.response import Response
from litestar.response.template import Template

from wuzzln.data import Game, PlayerId, get_season
from wuzzln.database import exists
from wuzzln.rating import compute_ratings, get_rank


@get("/player/{id: str}")
async def get_player_page(id: PlayerId, db: sqlite3.Connection, now: datetime) -> Response:
    player = id
    if not exists(db, "player", "id", player):
        raise NotFoundException("Player does not exist")
    player_name = db.execute("SELECT name FROM player WHERE id = ?", (player,)).fetchone()[0]

    season = get_season(now)
    games = tuple(
        Game(*r)
        for r in db.execute("SELECT * FROM game WHERE season = ? ORDER BY timestamp", (season,))
    )

    ratings = [r for r in reversed(compute_ratings(games)) if r.player == player]
    cur_defense = 0
    cur_offense = 0
    cur_rank = get_rank(0)
    if ratings:
        r = ratings[0]
        cur_defense = r.defense
        cur_offense = r.offense
        cur_rank = get_rank(r.overall)

    return Template(
        "player.html",
        context={
            "name": player_name,
            "rank": cur_rank,
            "defense_skill": cur_defense,
            "offense_skill": cur_offense,
            "season_games": f"{len(ratings):,d}",
        },
    )
