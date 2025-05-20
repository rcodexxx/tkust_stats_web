import enum
from sqlalchemy import Enum as SQLAlchemyEnum

class GenderEnum(enum.Enum):
    MALE = "男"
    FEMALE = "女"
    def __str__(self): return self.value

class PositionEnum(enum.Enum):
    BACK = "後排"
    FRONT = "前排"
    VERSATILE = "皆可"
    def __str__(self): return self.value

class MatchTypeEnum(enum.Enum):
    SINGLES = "單打"
    DOUBLES = "雙打"
    MIXED_DOUBLES = "混雙"
    def __str__(self): return self.value

class OverallMatchNatureEnum(enum.Enum):
    FRIENDLY = "友誼賽"
    INTERNAL_RANKING = "隊內排名賽"
    PRACTISE = "練習賽"
    NIAG = "全大運" #National Intercollegiate Athletic Games
    def __str__(self): return self.value

class OutcomeEnum(enum.Enum):
    WIN = "勝"
    LOSS = "負"
    NOT_PLAYED = "未比賽"
    def __str__(self): return self.value