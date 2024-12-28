import sqlite3
from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from typing import Mapping

from litestar import get
from litestar.response import Template

from wuzzln.data import Game, PlayerId, get_season
from wuzzln.database import query_game_count
from wuzzln.statistics import (
    compute_1v1_count,
    compute_game_count,
    compute_unique_people_count,
    compute_zero_score_count,
)


@dataclass
class Award:
    emoji: str
    title: str
    description: str
    player: PlayerId


def compute_player_awards(
    games: Iterable[Game], prior_game_count: Mapping[PlayerId, int]
) -> list[Award]:
    """Get all awards that relate to the game scores

    :param games: list of games
    :param prior_game_count: games each player played prior to the current games
    :return: list of awards
    """
    awards = []
    if game_count := compute_game_count(games):
        player, count = game_count.most_common(1)[0]
        awards.append(Award("🚵", "Going Pro", f"Played {count:,d} games", player))

    if unique_people_count := compute_unique_people_count(games):
        player, count = unique_people_count.most_common(1)[0]
        awards.append(Award("🌍", "Globalist", f"Played with {count:,d} different people", player))

    if one_v_ones := compute_1v1_count(games):
        player, count = one_v_ones.most_common(1)[0]
        awards.append(Award("🐺", "Lonewolf", f"Played {count:,d} 1v1s", player))

    if crawl_count := compute_zero_score_count(games, prior_game_count, "loss"):
        player, count = crawl_count.most_common(1)[0]
        awards.append(Award("🩸", "Knee Bleeder", f"Crawled {count:,d} times", player))

    if reverse_crawl_count := compute_zero_score_count(games, prior_game_count, "win"):
        player, count = reverse_crawl_count.most_common(1)[0]
        awards.append(Award("😈", "Ruthless", f"Let others crawl {count:,d} times", player))

    return awards


@get("/wrapped")
async def get_wrapped_page(db: sqlite3.Connection, now: datetime) -> Template:
    season = get_season(now)

    query = "SELECT * FROM game WHERE season = ? ORDER BY timestamp"
    season_games = tuple(Game(*row) for row in db.execute(query, (season,)))

    pre_season_game_count = query_game_count(
        db, season_games[0].timestamp if season_games else now.timestamp()
    )
    awards = compute_player_awards(season_games, pre_season_game_count)

    # TODO: most increase in games
    # TODO: total games, number of people who participated (+ change from last year)
    #       avg game increase per person, rating distribution changes???

    player_name = dict(db.execute("SELECT id, name FROM player"))

    return Template(
        "wrapped.html",
        context={"player_name": player_name, "season": "", "awards": awards},
    )
