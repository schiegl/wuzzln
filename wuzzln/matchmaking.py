import math
import random
from functools import lru_cache
from itertools import chain, combinations
from typing import Sequence

import trueskill as ts

type Team[Player] = tuple[Player, Player]

# team assignment representation e.g. [def_a, off_a, def_b, off_b, ...]
type Solution[Player] = tuple[Player, ...]


def as_teams[P](players: Solution[P]) -> set[Team[P]]:
    """Convert list of players to teams."""
    return {(players[i], players[i + 1]) for i in range(0, len(players), 2)}


def build_random_teams[P](players: Solution[P]) -> set[Team[P]]:
    """Assemble teams by assigning players randomly.

    :param players: any number of players above 2
    :return: random teams
    """
    if len(players) == 1:
        return set()

    players = tuple(random.sample(players, len(players)))

    if len(players) == 2:
        return set(zip(players, players))
    else:
        # add random player to last team
        if len(players) % 2 == 1:
            players += (players[0],)

        return as_teams(players)


def win_probability(team_a: Team[ts.Rating], team_b: Team[ts.Rating]) -> float:
    """Probability of team a winning.

    :param team_a: player ratings for team a
    :param team_b: player ratings for team b
    :return: win probability between 0 and 1 for team a
    """
    delta_mu = sum(r.mu for r in team_a) - sum(r.mu for r in team_b)
    sum_sigma = sum(r.sigma**2 for r in chain(team_a, team_b))
    size = len(team_a) + len(team_b)
    denominator = math.sqrt(size * ts.BETA**2 + sum_sigma)
    ts_env = ts.global_env()
    return ts_env.cdf(delta_mu / denominator)


def swap_two_players_neighborhood[P](solution: Solution[P]) -> list[Solution[P]]:
    """All possible team assignments where two players are swapped.

    :param solution: player assigned to teams
    :return: solutions with players swapped
    """
    n = len(solution)
    if n < 2 and n % 2 != 0:
        raise ValueError("Invalid number of players for swapping players")

    candidates = []
    for i in range(n):
        for j in range(i + 1, n):
            candidate = list(solution)
            candidate[i], candidate[j] = candidate[j], candidate[i]
            candidates.append(tuple(candidate))
    return candidates


def push[K, V](ordered_set: dict[K, V], limit: int, key: K, value: V) -> None:
    """Add key-value pair to dict and remove oldest pair if above limit.

    :param ordered_set: some dictionary
    :param limit: maximum number of elements allowed in dict
    :param key: element to insert
    :param value: value accompanying key
    """
    ordered_set[key] = value
    if len(ordered_set) > limit:
        del ordered_set[next(iter(ordered_set))]


def tabu_search(
    defense: Sequence[ts.Rating],
    offense: Sequence[ts.Rating],
    k: int = 1,
    max_iter: int = 5000,
    tabu_size: int = 20,
) -> list[set[Team[int]]]:
    """Find pairings that result highest draw probability using Tabu Search.

    :param defense: defense ratings for all players (n)
    :param offense: offense ratings for all players (n)
    :param k: number of solutions to return
    :param max_iter: maximum search optimization steps
    :param tabu_size: last search steps to remember and not visit again
    :raise ValueError: incorrect number of ratings
    :return: top team assignments with players named by their index in `defense` and `offense`
    """
    if k < 1:
        raise ValueError("k < 1 returns no solutions")
    elif max_iter < 1:
        raise ValueError("No optimization can happen if no iterations allowed")
    elif tabu_size < 1:
        raise ValueError("Tabu list length must be at least 1")

    if len(defense) != len(offense):
        raise ValueError("Each player must have defense and offense rating")
    elif len(defense) < 2:
        return []
    elif len(defense) == 2:
        return [{(p, p) for p in random.sample([0, 1], 2)} for _ in range(k)]

    @lru_cache(10_000)
    def draw_prob(team_a: Team[int], team_b: Team[int]) -> float:
        """Compute draw probability of matchup."""
        return ts.quality(
            [
                (defense[team_a[0]], offense[team_a[1]]),
                (defense[team_b[0]], offense[team_b[1]]),
            ]
        )

    def fitness(solution: Solution[int]) -> float:
        """Sum of squared draw probabilities between all team match ups."""
        teams = sorted(as_teams(solution))  # sorting reduces cache misses for draw_prob
        prob = sum(draw_prob(a, b) ** 2 for a, b in combinations(teams, 2))
        return prob

    # start with random solution
    candidate = tuple(random.sample(range(len(defense)), len(defense)))
    best_fitness = fitness(candidate)
    # using dicts for fast lookup + keeping order
    best_candidates = {candidate: best_fitness}
    tabu = {candidate: True}

    for _ in range(max_iter):
        neighborhood = swap_two_players_neighborhood(candidate)
        # if no better candidate found -> using random best candidate
        candidate = random.choice(neighborhood)
        candidate_fitness = fitness(candidate)
        for neighbor in neighborhood:
            if neighbor not in tabu:
                neighbor_fitness = fitness(neighbor)
                if neighbor_fitness > candidate_fitness:
                    candidate = neighbor
                    candidate_fitness = neighbor_fitness

        if candidate_fitness > best_fitness:
            best_fitness = candidate_fitness
            # because we only add better candidates top_candidates keeps fitness order
            push(best_candidates, k, candidate, candidate_fitness)

        # maintain maximum tabu list size
        push(tabu, tabu_size, candidate, True)

    return [as_teams(c) for c in reversed(best_candidates)]
