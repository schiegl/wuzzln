import sqlite3
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from random import randint, random
from typing import Mapping

from litestar import Request, get
from litestar.datastructures import Cookie
from litestar.exceptions import NotFoundException
from litestar.response import Template

from wuzzln.data import Game, PlayerId, Rating, get_season
from wuzzln.database import query_game_count
from wuzzln.rating import compute_ratings, get_latest_rating
from wuzzln.statistics import (
    compute_1v1_count,
    compute_game_count,
    compute_unique_people_count,
    compute_zero_score_count,
)


@dataclass
class Kpi:
    title: str
    value: float | int
    diff_relative: float
    footnote: str | None = None


@dataclass
class Placing:
    player: PlayerId
    skill_defense: float
    skill_offense: float


@dataclass
class Award:
    emoji: str
    title: str
    description: str
    players: list[PlayerId]


def compute_kpis(
    games: tuple[Game, ...],
    prev_games: tuple[Game, ...],
    prior_game_count: Counter[PlayerId],
    prior_prev_game_count: Counter[PlayerId],
) -> list[Kpi]:
    kpis = []

    def get_work_days(games):
        num_players = sum(len({g.defense_a, g.offense_a, g.defense_b, g.offense_b}) for g in games)
        return (num_players * 10) / (60 * 8)

    work_days = get_work_days(games)
    prev_work_days = get_work_days(prev_games)
    kpis.append(
        Kpi(
            "Total time played (days)*",
            round(work_days, 1),
            (work_days - prev_work_days) / prev_work_days if prev_work_days != 0 else 0,
            "* Assuming an 8h work day and 10 minutes per game",
        )
    )

    def get_unique_player_count(games):
        return len({p for g in games for p in {g.defense_a, g.offense_b, g.defense_b, g.offense_b}})

    player_count = get_unique_player_count(games)
    prev_player_count = get_unique_player_count(prev_games)
    kpis.append(
        Kpi(
            "Total players",
            player_count,
            (player_count - prev_player_count) / prev_player_count if prev_player_count != 0 else 0,
        )
    )

    kpis.append(
        Kpi(
            "Complaints about rating algorithm correctness**",
            randint(30, 40),
            random() * 0.3,
            "** Out of those, 0 took up my proposal to read the code",
        )
    )

    crawl_count = sum(compute_zero_score_count(games, prior_game_count, "loss").values())
    prev_crawl_count = sum(
        compute_zero_score_count(prev_games, prior_prev_game_count, "loss").values()
    )
    kpis.append(
        Kpi(
            "Table underside inspections",
            crawl_count,
            (crawl_count - prev_crawl_count) / prev_crawl_count if prev_crawl_count != 0 else 0,
        )
    )

    return kpis


def get_top_counts[K](counter: Counter[K], k=2) -> tuple[int, list[K]]:
    """Get maximum counts and return k on ties.

    :param counter: some counter
    :param k: how many ties to return
    :return: count, keys which got count
    """
    top_count = 0
    keys = []
    for key, count in counter.most_common(k):
        if top_count > 0 and count < top_count:
            break
        top_count = count
        keys.append(key)
    return top_count, keys


def compute_player_awards(
    games_sorted: tuple[Game, ...],
    prev_games_sorted: tuple[Game, ...],
    prior_game_count: Mapping[PlayerId, int],
) -> list[Award]:
    """Get all awards that relate to the game scores

    :param games_sorted: games from season
    :param prev_games_sorted: games from previous season
    :param prior_game_count: games each player played prior to the current games
    :return: list of awards
    """
    awards = []
    if game_count := compute_game_count(games_sorted):
        count, players = get_top_counts(game_count)
        awards.append(Award("🧗", "Going Pro", f"Played {count:,d} games", players))

    if unique_people_count := compute_unique_people_count(games_sorted):
        count, players = get_top_counts(unique_people_count)
        awards.append(Award("🌍", "Globalist", f"Played with {count:,d} different people", players))

    if one_v_ones := compute_1v1_count(games_sorted):
        count, players = get_top_counts(one_v_ones)
        awards.append(Award("🐺", "Lonewolf", f"Played {count:,d} 1v1s", players))

    if crawl_count := compute_zero_score_count(games_sorted, prior_game_count, "loss"):
        count, players = get_top_counts(crawl_count)
        awards.append(
            Award("🩸", "Knee Bleeder", f"Crawled {count:,d} times under the table", players)
        )

    if reverse_crawl_count := compute_zero_score_count(games_sorted, prior_game_count, "win"):
        count, players = get_top_counts(reverse_crawl_count)
        awards.append(Award("🦅", "Opportunist", f"Let others crawl {count:,d} times", players))

    if games_sorted:
        rating = {}
        prev_rating = {}
        for r in reversed(compute_ratings(games_sorted)):
            if r.player not in rating:
                rating[r.player] = r.overall
        for r in reversed(compute_ratings(prev_games_sorted)):
            if r.player not in prev_rating:
                prev_rating[r.player] = r.overall

        game_count = compute_game_count(prev_games_sorted)
        prev_game_count = compute_game_count(prev_games_sorted)
        rating_diff = [
            (rating[p] - prev_rating[p], p)
            for p in rating.keys()
            if p in prev_rating and game_count[p] >= 5 and prev_game_count[p] >= 5
        ]
        if rating_diff:
            diff, player = max(rating_diff)
            if diff > 3:
                award = Award("🌞", "Glow-up", f"Gained {diff:.1f} rating points", [player])
                awards.append(award)
            diff, player = min(rating_diff)
            if diff < -4:
                award = Award("🕳️", "Down Bad", f"Lost {abs(diff):.1f} rating points", [player])
                awards.append(award)

    return awards


@get("/wrapped")
async def get_wrapped_page(db: sqlite3.Connection, now: datetime) -> Template:
    query = "SELECT * FROM game WHERE season = ? ORDER BY timestamp"
    last_season_games = tuple(Game(*row) for row in db.execute(query, (get_season(now, -1),)))
    llast_season_games = tuple(Game(*row) for row in db.execute(query, (get_season(now, -2),)))

    if not last_season_games:
        raise NotFoundException("There were no games played in this time period")

    pre_last_season_game_count = query_game_count(db, last_season_games[0].timestamp)
    pre_llast_season_game_count = (
        query_game_count(db, llast_season_games[0].timestamp) if llast_season_games else Counter()
    )
    awards = compute_player_awards(
        last_season_games, llast_season_games, pre_last_season_game_count
    )

    kpis = compute_kpis(
        last_season_games,
        llast_season_games,
        pre_last_season_game_count,
        pre_llast_season_game_count,
    )

    # TODO: add awards to player page

    last_rating = get_latest_rating(last_season_games)
    top_3 = sorted(last_rating.items(), key=lambda x: x[1].overall, reverse=True)[:3]
    placing = [Placing(p, r.defense, r.offense) for p, r in top_3]

    player_name = dict(db.execute("SELECT id, name FROM player"))
    row = db.execute(
        "SELECT count(distinct season) FROM game WHERE timestamp <= ?",
        (last_season_games[0].timestamp,),
    ).fetchone()
    season_count = row[0] if row else 0

    return Template(
        "wrapped.html",
        context={
            "player_name": player_name,
            "season_count": season_count,
            "kpis": kpis,
            "placing": placing,
            "awards": awards,
        },
        cookies=[
            Cookie("wuzzln-wrapped", value=get_season(now), secure=True, max_age=3600 * 24 * 7)
        ],
    )
