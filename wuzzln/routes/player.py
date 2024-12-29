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

    # rating history
    query = "SELECT * FROM game WHERE season = ? ORDER BY timestamp"
    season_games = tuple(Game(*row) for row in db.execute(query, (get_season(now),)))
    season_ratings = compute_ratings(season_games)
    player_ratings_season = [r for r in season_ratings if r.player == player]

    # current skill
    defense_skill, offense_skill, overall_skill = 0, 0, 0
    if player_ratings_season:
        r = player_ratings_season[-1]
        defense_skill = r.defense
        offense_skill = r.offense
        overall_skill = r.overall

    # total games
    row = db.execute("SELECT count(*) FROM rating WHERE player = ?", (player,)).fetchone()
    total_games = (row[0] or 0) + len(player_ratings_season)

    # best skill
    row = db.execute("SELECT max(overall) FROM rating WHERE player = ?", (player,)).fetchone()
    best_skill = max(overall_skill, row[0] or 0)

    name = db.execute("SELECT name FROM player WHERE id = ?", (player,)).fetchone()[0]

    rows = db.execute(
        """
        WITH season_rating AS (
            SELECT season, overall, timestamp, ROW_NUMBER() OVER (PARTITION BY season ORDER BY timestamp DESC) as idx
            FROM rating
            WHERE player = ?
        )
        SELECT season, overall
        FROM season_rating
        WHERE idx == 1
        ORDER BY timestamp
    """,
        (player,),
    ).fetchall()
    all_seasons_ratings = [{"season": s, "rating": r} for s, r in rows]

    return Template(
        "player.html",
        context={
            "name": name,
            "rank": get_rank(overall_skill),
            "best_skill": best_skill,
            "defense_skill": defense_skill,
            "offense_skill": offense_skill,
            "total_games": f"{total_games:,d}",
            "all_seasons_ratings": all_seasons_ratings,
        },
    )
