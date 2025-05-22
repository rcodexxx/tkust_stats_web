from enum import StrEnum
from sqlalchemy import Enum as SQLAlchemyEnum

class GenderEnum(StrEnum):
    MALE = "男"
    FEMALE = "女"

    @classmethod
    def get_by_name(cls, name_str: str):
        if not name_str:
            return None
        try:
            return cls[name_str.upper()]  # 透過成員名稱 (key) 獲取 Enum 成員
        except KeyError:
            return None

class PositionEnum(StrEnum):
    BACK = "後排"
    FRONT = "前排"
    VERSATILE = "皆可"

    @classmethod
    def get_by_name(cls, name_str: str):
        if not name_str:
            return None
        try:
            return cls[name_str.upper()]
        except KeyError:
            return None

class MatchTypeEnum(StrEnum):
    SINGLES = "單打"
    DOUBLES = "雙打"
    MIXED_DOUBLES = "混雙"

    @classmethod
    def get_by_name(cls, name_str: str):
        if not name_str:
            return None
        try:
            return cls[name_str.upper()]
        except KeyError:
            return None

class OverallMatchNatureEnum(StrEnum):
    FRIENDLY = "友誼賽"
    INTERNAL_RANKING = "隊內排名賽"
    PRACTISE = "練習賽"
    NIAG = "全大運" #National Intercollegiate Athletic Games

    @classmethod
    def get_by_name(cls, name_str: str):
        if not name_str:
            return None
        try:
            return cls[name_str.upper()]
        except KeyError:
            return None

class OutcomeEnum(StrEnum):
    WIN = "勝"
    LOSS = "負"
    NOT_PLAYED = "未比賽"

    @classmethod
    def get_by_name(cls, name_str: str):
        if not name_str:
            return None
        try:
            return cls[name_str.upper()]
        except KeyError:
            return None