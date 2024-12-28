from collections import Counter

from wuzzln.data import Game
from wuzzln.statistics import (
    compute_1v1_count,
    compute_game_count,
    compute_streak,
    compute_zero_score_count,
)


def as_game(
    def_a,
    off_a,
    def_b,
    off_b,
    score_a,
    score_b,
    id="id",
    timestamp=0,
    org="org",
    season="season",
) -> Game:
    return Game(
        id=id,
        timestamp=timestamp,
        org=org,
        season=season,
        defense_a=def_a,
        offense_a=off_a,
        defense_b=def_b,
        offense_b=off_b,
        score_a=score_a,
        score_b=score_b,
    )


def test_game_count():
    games = [
        as_game("a", "b", "c", "d", 5, 1),
        as_game("a", "b", "c", "d", 5, 3),
        as_game("a", "b", "e", "f", 5, 3),
    ]
    assert compute_game_count(games) == Counter({"a": 3, "b": 3, "c": 2, "d": 2, "e": 1, "f": 1})


def test_1v1_count():
    games = [
        as_game("a", "a", "b", "b", 5, 1),
        as_game("a", "b", "c", "d", 5, 1),
        as_game("a", "a", "c", "c", 5, 1),
    ]
    assert compute_1v1_count(games) == Counter({"a": 2, "b": 1, "c": 1, "d": 0})


def test_1v1_game_count_not_counted_twice():
    games = [
        as_game("a", "a", "b", "b", 5, 1),
        as_game("a", "a", "b", "b", 5, 1),
    ]
    assert compute_game_count(games) == Counter({"a": 2, "b": 2})


def test_no_zero_score_count():
    games = [
        as_game("a", "b", "c", "d", 5, 1),
        as_game("a", "b", "c", "d", 5, 3),
    ]
    prior = {"a": 25, "b": 25, "c": 25, "d": 25}
    assert compute_zero_score_count(games, prior, "win", min_game_count=25) == Counter({})
    assert compute_zero_score_count(games, prior, "loss", min_game_count=25) == Counter({})


def test_zero_score_with_single_player_below_min_game_count():
    games = [
        as_game("a", "b", "c", "d", 5, 0),
        as_game("a", "b", "c", "d", 0, 1),
    ]
    prior = {"a": 25, "b": 25, "c": 24, "d": 25}
    # first win doesn't count because c is below 25 games
    assert compute_zero_score_count(games, prior, "win", min_game_count=25) == Counter(
        {"c": 1, "d": 1}
    )
    assert compute_zero_score_count(games, prior, "loss", min_game_count=25) == Counter(
        {"a": 1, "b": 1}
    )


def test_zero_score_reach_min_game_count_during_games():
    games = [
        as_game("a", "b", "c", "d", 5, 0),
        as_game("a", "b", "c", "d", 5, 0),
    ]
    prior = {"a": 25, "b": 25, "c": 24, "d": 25}
    assert compute_zero_score_count(games, prior, "win", min_game_count=25) == Counter(
        {"a": 1, "b": 1}
    )
    assert compute_zero_score_count(games, prior, "loss", min_game_count=25) == Counter(
        {"c": 1, "d": 1}
    )


def test_streak_non_contiguous():
    games = [
        as_game("a", "b", "c", "d", 5, 1),
        as_game("c", "d", "e", "f", 5, 1),
        as_game("a", "b", "e", "f", 5, 1),
    ]
    assert compute_streak(games, "win") == Counter({"a": 2, "b": 2, "c": 1, "d": 1, "e": 0, "f": 0})
    assert compute_streak(games, "loss") == Counter(
        {"a": 0, "b": 0, "c": 0, "d": 0, "e": 2, "f": 2}
    )


def test_streak_reset():
    games = [
        as_game("a", "b", "c", "d", 5, 1),
        as_game("a", "b", "c", "d", 5, 1),
        as_game("a", "b", "c", "d", 2, 3),
        as_game("a", "b", "c", "d", 5, 1),
    ]
    assert compute_streak(games, "win") == Counter({"a": 1, "b": 1, "c": 0, "d": 0})
    assert compute_streak(games, "loss") == Counter({"a": 0, "b": 0, "c": 1, "d": 1})
