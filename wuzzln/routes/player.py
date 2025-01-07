import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Mapping

from litestar import get
from litestar.exceptions import NotFoundException
from litestar.response.template import Template

from wuzzln.data import Game, PlayerId, get_season
from wuzzln.database import exists
from wuzzln.rating import get_latest_rating, get_rank
from wuzzln.statistics import compute_game_count, compute_zero_score_count


@dataclass
class Award:
    emoji: str
    title: str
    description: str


class Challenge:
    def __init__(self, emoji: str, title: str, current: int, goal: int):
        self.emoji = emoji
        self.title = title
        self.goal = goal
        self.absolute = min(goal, current)
        self.percentage = int(100 * (self.absolute / goal))


def get_awards(
    player: PlayerId, games_sorted: tuple[Game, ...], prior_game_count: Mapping[PlayerId, int]
):
    season_game_count = compute_game_count(games_sorted).get(player, 0)
    total_game_count = prior_game_count.get(player, 0) + season_game_count
    zero_wins = compute_zero_score_count(games_sorted, prior_game_count, mode="win").get(player, 0)
    zero_losses = compute_zero_score_count(games_sorted, prior_game_count, mode="loss").get(
        player, 0
    )

    return [
        Award("🧗", "Season Games", f"{season_game_count:,d}"),
        Award("⚽️", "Total Games", f"{total_game_count:,d}"),
        Award("🦅", "Let others crawl", f"{zero_wins:,d}"),
        Award("🩸", "Crawled", f"{zero_losses:,d}"),
    ]


def get_season_challenges(player: PlayerId, games_sorted: tuple[Game, ...]):
    defense_wins = 0
    offense_wins = 0
    unique_players = set()
    win_streak = 0
    max_win_streak = 0
    for g in games_sorted:
        if player == g.defense_a or player == g.defense_b:
            if g.defense_a != g.offense_a:
                defense_wins += 1
            is_win = g.score_a > g.score_b
        elif player == g.offense_a or player == g.offense_b:
            if g.defense_b != g.offense_b:
                offense_wins += 1
            is_win = g.score_b > g.score_a
        else:
            continue

        unique_players |= {g.defense_a, g.offense_a, g.defense_b, g.offense_b}
        win_streak = (win_streak + int(is_win)) * int(is_win)
        if win_streak > max_win_streak:
            max_win_streak = win_streak

    achievements = [
        Challenge("🛡️", "Win 25 games as defense", defense_wins, 25),
        Challenge("🗡️", "Win 25 games as offense", offense_wins, 25),
        Challenge("🌍", "Play with 20 different people", len(unique_players - {player}), 20),
        Challenge("🎢", "Win 12 times in a row", max_win_streak, 12),
    ]

    return achievements


@get("/player/{id: str}")
async def get_player_page(id: PlayerId, db: sqlite3.Connection, now: datetime) -> Template:
    player = id
    if not exists(db, "player", "id", player):
        raise NotFoundException("Player does not exist")
    player_name = db.execute("SELECT name FROM player WHERE id = ?", (player,)).fetchone()[0]

    season = get_season(now)
    games = tuple(
        Game(*r)
        for r in db.execute("SELECT * FROM game WHERE season = ? ORDER BY timestamp", (season,))
    )

    cur_defense = 0
    cur_offense = 0
    cur_rank = get_rank(0)
    if r := get_latest_rating(games).get(player):
        cur_defense = r.defense
        cur_offense = r.offense
        cur_rank = get_rank(r.overall)

    # prior_game_count = query_game_count(db, games[0].timestamp if games else now.timestamp())
    challenges = get_season_challenges(player, games)

    return Template(
        "player.html",
        context={
            "name": player_name,
            "rank": cur_rank,
            "defense_skill": cur_defense,
            "offense_skill": cur_offense,
            "challenges": challenges,
        },
    )
