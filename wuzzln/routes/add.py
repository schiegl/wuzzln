import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Annotated
from uuid import uuid4

from litestar import Response, delete, get, post
from litestar.datastructures.state import ImmutableState
from litestar.enums import RequestEncodingType
from litestar.params import Body
from litestar.response import Template

from wuzzln import toast
from wuzzln.data import Game, PlayerId, get_season
from wuzzln.database import exists, insert


@get("/add")
async def get_add_game_page(
    db: sqlite3.Connection, now: datetime, state: ImmutableState
) -> Template:
    player_name = dict(db.execute("SELECT id, name FROM player WHERE active = true"))
    hour_ago = (now - timedelta(hours=1)).timestamp()
    matchups = [m for m in state["matchmakings"] if m.timestamp > hour_ago]
    return Template("add.html", context={"player_name": player_name, "matchmakings": matchups})


@dataclass
class GameDTO:
    defense_a: PlayerId
    offense_a: PlayerId
    defense_b: PlayerId
    offense_b: PlayerId
    score_a: int
    score_b: int


# using 200 instead of 204 so we can return an empty response for htmx DOM swap
@delete("/api/game/delete/{id:str}", status_code=200)
async def delete_game(id: str, db: sqlite3.Connection, now: datetime) -> Response:
    ten_min_ago = (now - timedelta(minutes=10)).timestamp()
    db.execute("DELETE FROM game WHERE id = ? AND timestamp > ?", (id, ten_min_ago))
    db.commit()
    return Response("")


@post("/api/game/create")
async def add_game(
    data: Annotated[GameDTO, Body(media_type=RequestEncodingType.URL_ENCODED)],
    db: sqlite3.Connection,
    now: datetime,
) -> Template:
    g = data
    if not (0 <= g.score_a <= 10 and 0 <= g.score_b <= 10):
        return toast.error("Score must be between 0 and 10")
    elif g.score_a == g.score_b:
        return toast.error("Games cannot end in draw")

    # 1v1s don't need to specify both players (this also works for empty strings!)
    def_a = g.defense_a or g.offense_a
    off_a = g.offense_a or g.defense_a
    def_b = g.defense_b or g.offense_b
    off_b = g.offense_b or g.defense_b

    if not (def_a and off_a and def_b and off_b):
        return toast.error("Each side must have at least one player")

    if {def_a, off_a} & {def_b, off_b}:
        return toast.error("Players must not play in both teams")

    for p in def_a, off_a, def_b, off_b:
        if not exists(db, "player", "id", p):
            return toast.error("Unknown player")

    game = Game(
        str(uuid4()),
        now.timestamp(),
        "org",  # FIXME: organization placeholder
        get_season(now),
        def_a,
        off_a,
        def_b,
        off_b,
        g.score_a,
        g.score_b,
    )
    insert(db, game)
    db.commit()

    return toast.success("Game successfully added")
