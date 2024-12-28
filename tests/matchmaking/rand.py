import random

from wuzzln.matchmaking import build_random_teams


def test_no_players():
    assert build_random_teams(tuple()) == set()


def test_two_players():
    random.seed(394)
    teams = build_random_teams((1, 2))
    assert len(teams) == 2
    (def_a, off_a), (def_b, off_b) = list(teams)
    assert def_a == off_a
    assert def_b == off_b
    assert def_a != def_b


def test_unique_players():
    random.seed(394)
    for i in range(4, 10, 2):
        players = tuple(range(i))
        teams = build_random_teams(players)
        players_after = [p for ps in teams for p in ps]
        assert len(set(players_after)) == len(players_after)


def test_even_players():
    random.seed(393)
    for i in range(2, 10, 2):
        players = tuple(range(i))
        teams = build_random_teams(players)
        players_after = [p for ps in teams for p in ps]
        assert players != players_after


def test_odd_players():
    random.seed(394)
    for i in range(3, 10, 2):
        players = tuple(range(i))
        teams = build_random_teams(players)
        players_after = [p for ps in teams for p in ps]
        assert len(players_after) % 2 == 0, "Team with only single player exists"
        assert set(players_after) == set(players), "Build team with unknown players"
        assert len(players_after) == len(players) + 1, "Build too many teams"
