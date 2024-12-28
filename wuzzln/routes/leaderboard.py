import sqlite3
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Mapping, NamedTuple

from cachetools import LRUCache, cached
from litestar import get
from litestar.response import Template

from wuzzln.data import Game, PlayerId, Rank, get_season
from wuzzln.rating import compute_ratings, get_rank
from wuzzln.statistics import (
    compute_game_count,
    compute_streak,
    compute_zero_loss_count,
)


class Badge(NamedTuple):
    emoji: str
    description: str


@dataclass
class LeaderboardEntry:
    player: PlayerId
    name: str
    rank: Rank
    skill_all: float  # overall skill
    skill_defense: float
    skill_offense: float
    skill_diff: float  # difference to previous overall skill
    badges: list[Badge]


def build_leaderboard(
    games_sorted: tuple[Game, ...],
    player_name: Mapping[PlayerId, str],
    prior_game_count: Counter[PlayerId],
    now: datetime,
) -> dict[PlayerId, LeaderboardEntry]:
    """Build leaderboard without badges.

    :param games_sorted: all games played sorted by timestamp
    :param player_name: names of players for each player id
    :param prior_game_count: number of games played before `games_sorted`
    :param now: current time
    :return: player to leaderboard entry mapping
    """
    ratings = compute_ratings(games_sorted)

    diffs, cur_rat = {}, {}
    for r in reversed(ratings):
        if r.player not in diffs:
            if r.player in cur_rat:
                cur_rat_overall = cur_rat[r.player].overall
                diffs[r.player] = cur_rat_overall - r.overall
            else:
                cur_rat[r.player] = r

    leaderboard = {}
    sorted_rat = sorted(cur_rat.items(), key=lambda x: x[1].overall, reverse=True)
    for p, r in sorted_rat:
        leaderboard[p] = LeaderboardEntry(
            p,
            player_name[p],
            get_rank(r.overall),
            r.overall,
            r.defense,
            r.offense,
            diffs.get(p, 0),
            [],
        )

    if leaderboard:
        e = max(leaderboard.values(), key=lambda e: abs(e.skill_defense - e.skill_offense))
        diff = abs(e.skill_defense - e.skill_offense)
        if diff > 10:
            if e.skill_defense > e.skill_offense:
                text = "Good defense, but offense is hard to watch"
            else:
                text = "Good offense, but defense is hard to watch"
            badge = Badge("🦄", f"One-trick Pony: {text}")
            e.badges.append(badge)

    if game_count := compute_game_count(games_sorted):
        for e in leaderboard.values():
            total_games = game_count[e.player] + prior_game_count[e.player]
            if total_games < 25:
                badge = Badge("🐣", f"Kücken: Practiced {total_games} times so far")
                e.badges.append(badge)

    ts_2w_ago = (now - timedelta(weeks=2)).timestamp()
    games_2w = (g for g in games_sorted if g.timestamp > ts_2w_ago)
    if game_count_2w := compute_game_count(games_2w):
        player, count = game_count_2w.most_common(1)[0]
        badge = Badge("🛌", f"Sleeps in the office: Asked {count} times if someone wants play")
        leaderboard[player].badges.append(badge)

    if crawl_count := compute_zero_loss_count(games_sorted, prior_game_count):
        player, count = crawl_count.most_common(1)[0]
        badge = Badge("🩸", f"Knee Bleeder: Inspected the underside of the table {count} times")
        leaderboard[player].badges.append(badge)

    if win_streak := compute_streak(games_sorted, "win"):
        player, count = win_streak.most_common(1)[0]
        if count > 3:
            badge = Badge("🎢", f"Unstoppable: Won {count} times in a row")
            leaderboard[player].badges.append(badge)

    if loss_streak := compute_streak(games_sorted, "loss"):
        player, count = loss_streak.most_common(1)[0]
        if count > 3:
            badge = Badge(
                "🏳️", f"Moral support: Kept their team mate company {count} times in a row"
            )
            leaderboard[player].badges.append(badge)

    return leaderboard


@cached(LRUCache(1), key=lambda _, timestamp: timestamp)
def query_game_count(db: sqlite3.Connection, timestamp: float) -> Counter[PlayerId]:
    """Get all games played before a timestamp.

    Cached because this is used on the front page

    :param db: game database
    :param timestamp: unix epoch timestamp
    :return: player id to game count
    """
    query = """
        SELECT p.id, count(*)
        FROM player AS p JOIN game AS g
            ON p.id IN (g.defense_a, g.offense_a, g.defense_b, g.offense_b)
        WHERE timestamp < ?
        GROUP BY p.id
    """
    return Counter(dict(db.execute(query, (timestamp,))))


@get("/")
async def get_leaderboard_page(db: sqlite3.Connection, now: datetime) -> Template:
    season = get_season(now)
    query = "SELECT * FROM game WHERE season = ? ORDER BY timestamp"
    season_games_sorted = tuple(Game(*row) for row in db.execute(query, (season,)))

    season_start_ts = season_games_sorted[0].timestamp if season_games_sorted else now.timestamp()
    prior_game_count = query_game_count(db, season_start_ts)

    player_name = dict(db.execute("SELECT id, name FROM player"))
    leaderboard = build_leaderboard(season_games_sorted, player_name, prior_game_count, now)

    return Template("leaderboard.html", context={"leaderboard": leaderboard})
