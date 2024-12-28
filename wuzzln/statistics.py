import operator
from collections import Counter, defaultdict
from typing import Iterable, Literal, Mapping

from wuzzln.data import Game, PlayerId


def compute_zero_score_count(
    games: Iterable[Game],
    prior_game_count: Mapping[PlayerId, int],
    mode: Literal["win", "loss"],
    min_game_count: int = 25,
) -> Counter[PlayerId]:
    """Count number of zero losses per player.

    :param games: some games
    :param prior_game_count: number of games played before `games`
    :param mode: whether to count wins/losses
    :param min_game_count: minimum number of games until zero loss is counted
    :return: player to zero losses count mapping
    """
    cur_game_count = defaultdict(int, prior_game_count)
    zero_count = defaultdict(int)

    for g in games:
        team_a = {g.defense_a, g.offense_a}
        team_b = {g.defense_b, g.offense_b}
        is_zero_game = g.score_a == 0 or g.score_b == 0
        if is_zero_game:
            sides = [(team_a, team_b, g.score_a), (team_b, team_a, g.score_b)]
            for team, other_team, score in sides:
                if (
                    mode == "win"
                    and score > 0  # other score must be 0!
                    and all(cur_game_count[p] >= min_game_count for p in other_team)
                ) or (
                    mode == "loss"
                    and score == 0  # other score must be >0!
                    and all(cur_game_count[p] >= min_game_count for p in team)
                ):
                    for p in team:
                        zero_count[p] += 1

        # count in case some players haven't reached min_game_count yet
        for p in team_a | team_b:
            cur_game_count[p] += 1

    return Counter(zero_count)


def compute_game_count(games: Iterable[Game]) -> Counter[PlayerId]:
    """Count number of games per player.

    :param games: some games
    :return: player to game count mapping
    """
    return Counter(p for g in games for p in {g.defense_a, g.offense_a, g.defense_b, g.offense_b})


def compute_unique_people_count(games: Iterable[Game]) -> Counter[PlayerId]:
    """Count number of unique people each player played with.

    :param games: some games
    :return: player to unique people count mapping
    """
    people_count = defaultdict(set)
    for g in games:
        players = {g.defense_a, g.offense_a, g.defense_b, g.offense_b}
        for p in players:
            people_count[p] |= players

    return Counter({player: len(people) for player, people in people_count.items()})


def compute_1v1_count(games: Iterable[Game]) -> Counter[PlayerId]:
    """Count number of 1v1s per player.

    :param games: some games
    :return: player to 1v1 count mapping
    """
    return Counter(
        p
        for g in games
        if g.defense_a == g.offense_a and g.defense_b == g.offense_b and g.defense_a != g.defense_b
        for p in (g.defense_a, g.defense_b)
    )


def compute_streak(games_sorted: Iterable[Game], mode: Literal["win", "loss"]) -> Counter[PlayerId]:
    """Count number of won/lost games in a row per player.

    :param games_sorted: sorted games
    :return: player to win/lost streak length mapping
    """
    win_streak = defaultdict(int)

    def add(team, won: bool):
        for p in team:
            win_streak[p] = (win_streak[p] + won) * won

    cmp = operator.gt if mode == "win" else operator.lt

    for g in games_sorted:
        add({g.defense_a, g.offense_a}, cmp(g.score_a, g.score_b))
        add({g.defense_b, g.offense_b}, cmp(g.score_b, g.score_a))

    return Counter(win_streak)
