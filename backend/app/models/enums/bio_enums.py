from __future__ import annotations

from .base import BaseEnum


class GenderEnum(BaseEnum):
    """性別"""

    MALE = "male"
    FEMALE = "female"


class BloodTypeEnum(BaseEnum):
    """血型"""

    A = "A"
    B = "B"
    AB = "AB"
    O = "O"
    UNKNOWN = "unknown"
