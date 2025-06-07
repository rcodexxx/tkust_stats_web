# your_app/enums/user_enums.py
from __future__ import annotations

from .base import BaseEnum


class UserRoleEnum(BaseEnum):
    """使用者角色"""

    ADMIN = "admin"
    MEMBER = "member"
    COACH = "coach"
    CADRE = "cadre"

    @property
    def permission_level(self) -> int:
        """根據角色返回一個權限等級 (範例)。"""
        if self == UserRoleEnum.ADMIN:
            return 4
        elif self == UserRoleEnum.COACH:
            return 3
        elif self == UserRoleEnum.CADRE:
            return 2
        elif self == UserRoleEnum.MEMBER:
            return 1
        return 0
