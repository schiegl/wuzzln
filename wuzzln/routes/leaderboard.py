import sqlite3
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Mapping, NamedTuple, Sequence

from litestar import get
from litestar.response import Template

from wuzzln.data import Game, PlayerId, Rank, get_season
from wuzzln.rating import compute_ratings, get_rank


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
    games_sorted: tuple[Game, ...], player_name: Mapping[PlayerId, str]
) -> dict[PlayerId, LeaderboardEntry]:
    """Build leaderboard without badges.

    :param games_sorted: all games played sorted by timestamp
    :param player_name: names of players for each player id
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

    return leaderboard


def add_badges_(
    leaderboard: Mapping[PlayerId, LeaderboardEntry],
    season_games: Sequence[Game],
    pre_season_games: dict[PlayerId, int],
    now: datetime,
):
    """Add badges to leaderboard in-place.

    :param leaderboard: all players in current leaderboard
    :param season_games: games of the current season
    :param pre_season_games: total number of games played in all previous seasons
    :param now: current time
    """
    # one-trick pony
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

    # compute some game statistics
    crawled = defaultdict(int)
    total_games = defaultdict(int, pre_season_games)
    total_games_two_weeks = defaultdict(int)
    two_weeks_ago = (now - timedelta(weeks=2)).timestamp()
    win_streak = defaultdict(int)
    loss_streak = defaultdict(int)

    for g in season_games:
        result = [
            ({g.defense_a, g.offense_a}, g.score_a, g.score_b),
            ({g.defense_b, g.offense_b}, g.score_b, g.score_a),
        ]
        for players, score, score_other in result:
            is_crawl = score == 0 and score_other > 0 and all(total_games[p] >= 25 for p in players)
            for p in players:
                if is_crawl:
                    crawled[p] += 1
                win_streak[p] = win_streak[p] + 1 if score > score_other else 0
                loss_streak[p] = loss_streak[p] + 1 if score < score_other else 0
                total_games[p] += 1
                if g.timestamp > two_weeks_ago:
                    total_games_two_weeks[p] += 1

    # knee bleeder
    if crawled:
        player, crawl_num = max(crawled.items(), key=lambda x: x[1])
        badge = Badge("🩸", f"Knee Bleeder: Inspected the underside of the table {crawl_num} times")
        leaderboard[player].badges.append(badge)

    # chicken status
    if total_games:
        for p in leaderboard.keys():
            num_games = total_games[p]
            if num_games < 25:
                badge = Badge("🐣", f"Kücken: Practiced {num_games} times so far")
                leaderboard[p].badges.append(badge)

    # sleeps in the office
    if total_games_two_weeks:
        player, num_games = max(total_games_two_weeks.items(), key=lambda x: x[1])
        badge = Badge("🛌", f"Sleeps in the office: Asked {num_games} times if someone wants play")
        leaderboard[player].badges.append(badge)

    # win streak
    if win_streak:
        player, num_wins = max(win_streak.items(), key=lambda x: x[1])
        if num_wins > 3:
            badge = Badge("🎢", f"Unstoppable: Won {num_wins} times in a row")
            leaderboard[player].badges.append(badge)

    # moral support
    if loss_streak:
        player, num_losses = max(loss_streak.items(), key=lambda x: x[1])
        if num_losses > 3:
            badge = Badge(
                "🏳️", f"Moral support: Kept their team mate company {num_wins} times in a row"
            )
            leaderboard[player].badges.append(badge)


@get("/")
async def get_leaderboard_page(db: sqlite3.Connection, now: datetime) -> Template:
    season = get_season(now)
    query = "SELECT * FROM game WHERE season = ? ORDER BY timestamp"
    season_games = tuple(Game(*row) for row in db.execute(query, (season,)))
    player_name = dict(db.execute("SELECT id, name FROM player"))
    leaderboard = build_leaderboard(season_games, player_name)

    pre_season_games = defaultdict(int)
    add_badges_(leaderboard, season_games, pre_season_games, now)

    return Template("leaderboard.html", context={"leaderboard": leaderboard})
