import math
import random
from itertools import combinations
from typing import Sequence

import trueskill as ts

from wuzzln.matchmaking import (
    build_random_teams,
    swap_two_players_neighborhood,
    tabu_search,
    win_probability,
)


def test_random_teams_two_players():
    random.seed(394)
    teams = build_random_teams((1, 2))
    assert len(teams) == 2
    (def_a, off_a), (def_b, off_b) = list(teams)
    assert def_a == off_a
    assert def_b == off_b
    assert def_a != def_b


def test_random_teams_unique_players():
    random.seed(394)
    for i in range(4, 10, 2):
        players = tuple(range(i))
        teams = build_random_teams(players)
        players_after = [p for ps in teams for p in ps]
        assert len(set(players_after)) == len(players_after)


def test_random_teams_with_even_players():
    random.seed(393)
    for i in range(2, 10, 2):
        players = tuple(range(i))
        teams = build_random_teams(players)
        players_after = [p for ps in teams for p in ps]
        assert players != players_after


def test_random_teams_with_odd_players():
    random.seed(394)
    for i in range(3, 10, 2):
        players = tuple(range(i))
        teams = build_random_teams(players)
        players_after = [p for ps in teams for p in ps]
        assert len(players_after) % 2 == 0, "Team with only single player exists"
        assert set(players_after) == set(players), "Build team with unknown players"
        assert len(players_after) == len(players) + 1, "Build too many teams"


def test_swap_two_player_neighborhood():
    players = tuple(range(4))
    neighborhood_expected = {
        # player 0 swapped
        (1, 0, 2, 3),
        (2, 1, 0, 3),
        (3, 1, 2, 0),
        # player 1 swapped
        (0, 2, 1, 3),
        (0, 3, 2, 1),
        # player 2 swapped
        (0, 1, 3, 2),
    }
    neighborhood = swap_two_players_neighborhood(players)

    assert set(neighborhood) == neighborhood_expected


def as_rating(mus: Sequence[float | int], sigma: float = 0.001) -> list[ts.Rating]:
    return [ts.Rating(mu, sigma) for mu in mus]


def test_tabu_search_unique_players():
    random.seed(394)
    for i in range(2, 10, 2):
        defense = as_rating([random.randrange(0, 30) for _ in range(i)])
        offense = as_rating([random.randrange(0, 30) for _ in range(i)])
        # run multiple times because tabu search uses randomness
        for _ in range(10):
            teams = tabu_search(defense, offense, max_iter=100)[0]
            players_after = [p for ps in teams for p in ps]
            assert len(set(players_after)) == len(players_after)


def test_tabu_search_simple():
    random.seed(394)
    defense = as_rating([5, 0, 5, 0])
    offense = as_rating([0, 5, 0, 5])
    bad_matchups = [
        # bad team, good team
        {(1, 0), (2, 3)},
        {(3, 2), (0, 1)},
        {(1, 2), (0, 3)},
    ]

    # run multiple times because tabu search uses randomness
    for _ in range(10):
        teams = tabu_search(defense, offense, max_iter=200)[0]
        assert teams not in bad_matchups


def test_tabu_search_two_good_players_not_in_same_team():
    random.seed(394)
    defense = as_rating([5, 0, 0, 0])
    offense = as_rating([0, 5, 0, 0])

    for _ in range(10):
        teams = tabu_search(defense, offense, max_iter=100)[0]
        for team in teams:
            assert team != (0, 1)


def test_tabu_search_ordered_solution():
    random.seed(389)
    for _ in range(10):
        defense = as_rating([random.randrange(0, 30) for _ in range(8)])
        offense = as_rating([random.randrange(0, 30) for _ in range(8)])

        avg_devs = []
        for teams in tabu_search(defense, offense, k=4, max_iter=500):
            print(teams)
            devs = []
            for team_a, team_b in combinations(sorted(teams), 2):
                team_a = (defense[team_a[0]], offense[team_a[1]])
                team_b = (defense[team_b[0]], offense[team_b[1]])
                fair_dev = abs(0.5 - win_probability(team_a, team_b))
                devs.append(fair_dev)
            avg_devs.append(sum(devs) / len(devs))

        # k is not exact at the moment
        assert 1 < len(avg_devs) <= 4
        assert sorted(avg_devs) == avg_devs
