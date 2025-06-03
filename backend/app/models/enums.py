from enum import StrEnum, Enum


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


class MatchNatureEnum(StrEnum):
    FRIENDLY = "友誼賽"
    INTERNAL_RANKING = "隊內排名賽"
    PRACTISE = "練習賽"
    NIAG = "全大運"  # National Intercollegiate Athletic Games

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
            return cls[name_str]
        except KeyError:
            return None


class MatchFormatEnum(StrEnum):
    TIEBREAK = "搶七"
    FIVE_GAME_SET = "五局制"
    SEVEN_GAME_SET = "七局制"
    NINE_GAME_SET = "九局制"

    @classmethod
    def get_by_name(cls, name_str: str):
        if not name_str:
            return None
        try:
            return cls[name_str]
        except KeyError:
            return None


class UserRoleEnum(Enum):
    MEMBER = ("隊員", 1)
    CADRE = ("幹部", 2)
    COACH = ("教練", 3)
    ADMIN = ("管理員", 4)

    # 讓 Enum 實例可以直接訪問 display_name 和 level
    def __init__(self, display_name, level):
        self._display_name_val = display_name  # 儲存中文名
        self.level = level

    @property
    def display_name(self):  # 提供一個 property 來獲取中文名
        return self._display_name_val

    @classmethod
    def get_by_name(cls, name_str: str):
        if not name_str:
            return None
        try:
            return cls[name_str]
        except KeyError:
            return None

    # 讓 str(UserRoleEnum.PLAYER) 返回 "隊員" (Enum 的 value 會是 tuple)
    # Naive UI 的 NTag 等通常使用 label，所以 User.to_dict() 中回傳 role.display_name
    def __str__(self):
        return self.display_name
