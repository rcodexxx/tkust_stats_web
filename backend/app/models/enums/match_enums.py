# your_app/enums/match_enums.py
from __future__ import annotations

from .base import BaseEnum


class MatchTypeEnum(BaseEnum):
    """比賽類型 (單打、雙打、混雙)"""

    SINGLES = "singles"
    DOUBLES = "doubles"
    MIXED_DOUBLES = "mixed_doubles"


class MatchOutcomeEnum(BaseEnum):
    """比賽結果"""

    WIN = "win"
    LOSS = "loss"
    PENDING = "pending"


class MatchFormatEnum(BaseEnum):
    """比賽賽制"""

    GAMES_5 = "games_5"
    GAMES_7 = "games_7"
    GAMES_9 = "games_9"


class MatchPositionEnum(BaseEnum):
    """球員比賽位置 (前排、後排)"""

    FRONT = "front"
    BACK = "back"
    VERSATILE = "versatile"


class MatchNatureEnum(BaseEnum):
    """比賽性質 (友誼賽、排名賽等)"""

    FRIENDLY = "friendly"
    INTERNAL_RANKING = "internal_ranking"
    PRACTICE = "practice"
    NIAG = "NIAG"  # National Intercollegiate Athletic Games (全大運)
