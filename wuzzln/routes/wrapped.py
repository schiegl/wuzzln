import sqlite3
from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from litestar import get
from litestar.connection import ASGIConnection
from litestar.exceptions import NotAuthorizedException
from litestar.handlers import BaseRouteHandler
from litestar.response import Template

from wuzzln.data import Game, PlayerId, SeasonId, get_season


@dataclass
class Award:
    emoji: str
    title: str
    description: str
    player: PlayerId


def get_player_awards(games: Iterable[Game], prior_game_count: dict[PlayerId, int]) -> list[Award]:
    """Get all awards that relate to the game scores

    :param games: list of games
    :param prior_game_count: games each player played prior to the current games
    :return: list of awards
    """
    total_games = defaultdict(int)
    total_1v1s = defaultdict(int)
    total_crawls = defaultdict(int)
    total_let_crawls = defaultdict(int)
    total_played_others = defaultdict(set)

    for g in games:
        # total games
        players = {g.defense_a, g.offense_a, g.defense_b, g.offense_b}
        for p in players:
            total_games[p] += 1
            total_played_others[p] = total_played_others[p] | players

        # 1v1s
        if len(players) == 2:
            for p in players:
                total_1v1s[p] += 1

        # crawling
        team_a = {g.defense_a, g.offense_a}
        team_b = {g.defense_b, g.offense_b}
        result = [(team_a, team_b, g.score_a, g.score_b), (team_b, team_a, g.score_b, g.score_a)]
        for players, other_players, score, other_score in result:
            if (
                score == 0
                and other_score > 0
                and all(total_games.get(p, 0) + prior_game_count.get(p, 0) >= 25 for p in players)
            ):
                for p in players:
                    total_crawls[p] += 1
            if (
                other_score == 0
                and score > 0
                and all(
                    total_games.get(p, 0) + prior_game_count.get(p, 0) >= 25 for p in other_players
                )
            ):
                for p in players:
                    total_let_crawls[p] += 1

    awards = []
    if total_games:
        player = max(total_games, key=total_games.get)  # type: ignore
        awards.append(Award("🚵", "Going Pro", f"Played {total_games[player]:,d} games", player))

    if total_played_others:
        player = max(total_played_others, key=lambda p: len(total_played_others[p]))  # type: ignore
        awards.append(
            Award(
                "🌍",
                "Globalist",
                f"Played with {len(total_played_others[player]):,d} different people",
                player,
            )
        )

    if total_1v1s:
        player = max(total_1v1s, key=total_1v1s.get)  # type: ignore
        awards.append(Award("🐺", "Lonewolf", f"Played {total_1v1s[player]:,d} 1v1s", player))

    if total_crawls:
        player = max(total_crawls, key=total_crawls.get)  # type: ignore
        awards.append(
            Award("🩸", "Knee Bleeder", f"Crawled {total_crawls[player]:,d} times", player)
        )

    if total_let_crawls:
        player = max(total_let_crawls, key=total_let_crawls.get)  # type: ignore
        awards.append(
            Award("😈", "Ruthless", f"Let others crawl {total_let_crawls[player]:,d} times", player)
        )

    return awards


def is_season_start(ctx: Mapping[str, Any] | None = None) -> bool:
    """Check if season start.

    :param ctx: context of jinja template
    :return: true if new season
    """
    # TODO: replace with now
    now = datetime(year=2024, month=10, day=7)
    now_season = get_season(now)
    week_ago_season = get_season(now - timedelta(days=7))
    return now_season != week_ago_season


def season_start_guard(connection: ASGIConnection, route_handler: BaseRouteHandler):
    """Check if in wrapped period."""
    if not is_season_start():
        raise NotAuthorizedException("This is a seasonal thing :)")


@get("/wrapped", guards=[season_start_guard])
async def get_wrapped_page(db: sqlite3.Connection, now: datetime) -> Template:
    prev_season = get_season(now)

    query = "SELECT * FROM game WHERE season = ? ORDER BY timestamp"
    season_games = tuple(Game(*row) for row in db.execute(query, (prev_season,)))

    prior_game_count = defaultdict(
        int, db.execute("SELECT player, count(*) FROM rating GROUP BY player")
    )
    awards = get_player_awards(season_games, prior_game_count)

    # TODO: most increase in games
    # TODO: total games, number of people who participated (+ change from last year)
    #       avg game increase per person, rating distribution changes???

    player_name = dict(db.execute("SELECT id, name FROM player"))

    return Template(
        "wrapped.html",
        context={"player_name": player_name, "season": "", "awards": awards},
    )
