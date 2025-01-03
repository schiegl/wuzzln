from collections import defaultdict
from functools import lru_cache

import trueskill as ts

from wuzzln.data import Game, PlayerId, Rank, Rating


def get_rank(trueskill_mean: float) -> Rank:
    if trueskill_mean <= 0:
        return Rank.IRON
    elif trueskill_mean < 5:
        return Rank.BRONZE
    elif trueskill_mean < 10:
        return Rank.SILVER
    elif trueskill_mean < 15:
        return Rank.GOLD
    elif trueskill_mean < 20:
        return Rank.PLATINUM
    elif trueskill_mean < 26:
        return Rank.DIAMOND
    else:
        return Rank.IMMORTAL


@lru_cache(2)
def compute_ratings(games_sorted: tuple[Game, ...]) -> list[Rating]:
    """Compute rating history.

    :param games_sorted: games sorted by time (tuple allows caching!)
    :return: ratings sorted by time
    """
    def_rat = defaultdict(ts.Rating)
    off_rat = defaultdict(ts.Rating)
    hist = []

    for g in games_sorted:
        def_a, off_a, def_b, off_b = g.defense_a, g.offense_a, g.defense_b, g.offense_b
        team_a = def_rat[def_a], off_rat[off_a]
        team_b = def_rat[def_b], off_rat[off_b]

        (def_a_rat, off_a_rat), (def_b_rat, off_b_rat) = ts.rate(
            [team_a, team_b], [-g.score_a, -g.score_b]
        )
        def_rat[def_a] = def_a_rat
        off_rat[off_a] = off_a_rat
        def_rat[def_b] = def_b_rat
        off_rat[off_b] = off_b_rat

        players_ratings = [
            (def_a, def_a_rat, off_rat[def_a]),
            (def_b, def_b_rat, off_rat[def_b]),
        ]
        # avoid duplicate ratings in case 1v1 game
        if def_a != off_a:
            players_ratings.append((off_a, def_rat[off_a], off_a_rat))
        if def_b != off_b:
            players_ratings.append((off_b, def_rat[off_b], off_b_rat))

        for player, pdr, por in players_ratings:
            pd_skill = ts.expose(pdr)
            po_skill = ts.expose(por)
            p_skill = (pd_skill + po_skill) / 2
            hist.append(
                Rating(
                    g.season,
                    player,
                    g.timestamp,
                    p_skill,
                    pd_skill,
                    pdr.mu,
                    pdr.sigma,
                    po_skill,
                    por.mu,
                    por.sigma,
                )
            )

    return hist


def get_latest_rating(games_sorted: tuple[Game, ...]) -> dict[PlayerId, Rating]:
    """Get latest rating.

    :param games_sorted: games sorted by timestamp
    :return: player to rating mapping
    """
    last_rating = {}
    for r in reversed(compute_ratings(games_sorted)):
        if r.player not in last_rating:
            last_rating[r.player] = r
    return last_rating
