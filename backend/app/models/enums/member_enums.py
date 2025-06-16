# backend/app/models/enums/member_enums.py
from .base import BaseEnum


class GuestRoleEnum(BaseEnum):
    """訪客在比賽中的身份類型"""

    TEAMMATE = "teammate"  # 隊友：外出比賽的合作夥伴
    OPPONENT = "opponent"  # 對手：記錄比賽的對戰對手
    # SUBSTITUTE = "substitute"  # 替補：臨時替補球員
    NEUTRAL = "neutral"  # 中性：身份未明確

    @classmethod
    def get_display_name(cls, value):
        """獲取顯示名稱"""
        display_map = {
            cls.TEAMMATE: "隊友",
            cls.OPPONENT: "對手",
            # cls.SUBSTITUTE: "替補",
            cls.NEUTRAL: "訪客",
        }
        return display_map.get(value, "未知")

    @classmethod
    def get_description(cls, value):
        """獲取描述"""
        desc_map = {
            cls.TEAMMATE: "隊友",
            cls.OPPONENT: "對手",
            # cls.SUBSTITUTE: "臨時替補球員",
            cls.NEUTRAL: "訪客",
        }
        return desc_map.get(value, "未知身份")

    @classmethod
    def get_all_options(cls):
        """獲取所有選項（用於前端選擇器）"""
        return [
            {
                "value": cls.TEAMMATE,
                "label": cls.get_display_name(cls.TEAMMATE),
                # "description": cls.get_description(cls.TEAMMATE),
            },
            {
                "value": cls.OPPONENT,
                "label": cls.get_display_name(cls.OPPONENT),
                # "description": cls.get_description(cls.OPPONENT),
            },
            # {
            #     "value": cls.SUBSTITUTE,
            #     "label": cls.get_display_name(cls.SUBSTITUTE),
            #     "description": cls.get_description(cls.SUBSTITUTE),
            # },
            {
                "value": cls.NEUTRAL,
                "label": cls.get_display_name(cls.NEUTRAL),
                # "description": cls.get_description(cls.NEUTRAL),
            },
        ]
