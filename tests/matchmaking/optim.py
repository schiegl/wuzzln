import random
from itertools import combinations
from typing import Sequence

import trueskill as ts

from wuzzln.matchmaking import swap_two_players_neighborhood, tabu_search, win_probability


def as_rating(mus: Sequence[float | int], sigma: float = 0.001) -> list[ts.Rating]:
    return [ts.Rating(mu, sigma) for mu in mus]


def test_no_players():
    assert tabu_search([], []) == []


def test_two_players():
    assert tabu_search(as_rating([2, 3]), as_rating([4, 5])) == [{(0, 0), (1, 1)}]


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


def test_tabu_search_unique_players():
    random.seed(394)
    # starting at 4 because in 2 player scenario each player plays defense and offense
    for i in range(4, 10, 2):
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
