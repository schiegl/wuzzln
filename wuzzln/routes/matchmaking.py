import random
import sqlite3
import time
from collections import defaultdict
from dataclasses import dataclass
from itertools import combinations
from typing import Annotated, Literal, Sequence

import trueskill as ts
from litestar import get, post
from litestar.contrib.htmx.response import HTMXTemplate
from litestar.datastructures.state import State
from litestar.enums import RequestEncodingType
from litestar.params import Body
from litestar.response import Template

from wuzzln import toast
from wuzzln.data import Game, Matchmaking, PlayerId, get_season
from wuzzln.database import exists
from wuzzln.matchmaking import build_random_teams, tabu_search, win_probability
from wuzzln.rating import compute_ratings


@get("/matchmaking")
async def get_matchmaking_page(db: sqlite3.Connection) -> Template:
    player_name = dict(db.execute("SELECT id, name FROM player WHERE active = true"))
    return Template("matchmaking.html", context={"player_name": player_name})


def get_rating(
    games_sorted: tuple[Game, ...], players: Sequence[PlayerId]
) -> tuple[list[ts.Rating], list[ts.Rating]]:
    """Get current rating of player.

    :param games_sorted: sorted by timestamp ascending
    :param players: players to get rating from
    :return: defense, offense rating
    """
    players_set = set(players)
    ratings = compute_ratings(games_sorted)
    defense, offense = defaultdict(ts.Rating), defaultdict(ts.Rating)
    for r in reversed(ratings):
        if r.player in players_set and r.player not in defense:
            defense[r.player] = ts.Rating(r.defense_mu, r.defense_sigma)
            offense[r.player] = ts.Rating(r.offense_mu, r.offense_sigma)

    return [defense[p] for p in players], [offense[p] for p in players]


@dataclass
class MatchmakingTaskDTO:
    players: list[PlayerId]
    method: Literal["fair", "quite_fair", "random"]
    probability: Literal["on"] | None = None


@post("/api/matchmaking/create")
async def post_matchmaking(
    data: Annotated[MatchmakingTaskDTO, Body(media_type=RequestEncodingType.URL_ENCODED)],
    db: sqlite3.Connection,
    state: State,
) -> Template:
    players = data.players
    if len(players) < 2:
        return toast.error("At least 2 players necessary")
    elif len(players) % 2 != 0:
        return toast.error("Only even number of players supported")
    elif len(set(players)) != len(players):
        return toast.error("No duplicate players allowed")
    elif any(not exists(db, "player", "id", p) for p in players):
        return toast.error("Unknown player")

    query = "SELECT * FROM game WHERE season = ? ORDER BY timestamp"
    season_games = tuple(Game(*row) for row in db.execute(query, (get_season(),)))
    defense, offense = get_rating(season_games, players)

    match data.method:
        case "random":
            player_idx = tuple(range(len(players)))
            teams = build_random_teams(player_idx)
        case "fair":
            teams = tabu_search(defense, offense, k=1)[0]
        case "quite_fair":
            teams = random.choice(tabu_search(defense, offense, k=2))

    # build matchups
    matchmakings = []
    now = time.time()
    for (def_a, off_a), (def_b, off_b) in combinations(teams, 2):
        rat_a = (defense[def_a], offense[off_a])
        rat_b = (defense[def_b], offense[off_b])
        win_prob = win_probability(rat_a, rat_b)
        # TODO: add whether this is a rank up game
        m = Matchmaking(
            now,
            players[def_a],
            players[off_a],
            players[def_b],
            players[off_b],
            win_prob,
            1 - win_prob,
        )
        matchmakings.append(m)

    for m in matchmakings:
        state["matchmakings"].appendleft(m)

    player_name = dict(db.execute("SELECT id, name FROM player"))

    return HTMXTemplate(
        template_name="matchmaking_fragment.html",
        context={
            "player_name": player_name,
            "matchmakings": matchmakings,
            "show_probability": data.probability == "on",
        },
    )
