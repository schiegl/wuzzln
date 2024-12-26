import re
import unicodedata
from datetime import datetime
from enum import Enum
from typing import NamedTuple

type PlayerId = str
type Team = tuple[PlayerId, PlayerId]
type OrgId = str
type SeasonId = str
type Timestamp = float


class Rank(Enum):
    IRON = 0
    BRONZE = 1
    SILVER = 2
    GOLD = 3
    PLATINUM = 4
    DIAMOND = 5
    IMMORTAL = 6


class Player(NamedTuple):
    id: PlayerId
    org: OrgId
    name: str
    active: bool


class Game(NamedTuple):
    id: str
    timestamp: Timestamp
    org: OrgId
    season: SeasonId
    defense_a: PlayerId
    offense_a: PlayerId
    defense_b: PlayerId
    offense_b: PlayerId
    score_a: int
    score_b: int


class Rating(NamedTuple):
    season: SeasonId
    player: PlayerId
    timestamp: Timestamp
    overall: float
    defense: float
    defense_mu: float
    defense_sigma: float
    offense: float
    offense_mu: float
    offense_sigma: float


class Matchmaking(NamedTuple):
    timestamp: Timestamp
    defense_a: PlayerId
    offense_a: PlayerId
    defense_b: PlayerId
    offense_b: PlayerId
    win_probability_a: float
    win_probability_b: float


def clean_id(string: str) -> str:
    norm_str = (
        unicodedata.normalize("NFKD", string).encode("ascii", "ignore").decode("utf-8").lower()
    )
    return re.sub(r"[^a-z0-9_]", "", norm_str)


def get_season(now: datetime) -> SeasonId:
    return f"{now.year}-{(now.month - 1) // 3 + 1}"
