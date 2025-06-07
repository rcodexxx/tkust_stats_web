# your_app/enums/base.py
from __future__ import annotations

from enum import StrEnum
from typing import List, Tuple, Optional, TypeVar, Type

# _S 用於表示 BaseEnum 的子類別型別，確保型別提示的精確性
_S = TypeVar("_S", bound="BaseEnum")


class BaseEnum(StrEnum):
    """
    一個功能更完整的字串枚舉 (StrEnum) 基礎類別。
    它為所有繼承它的具體枚舉類別提供了一系列實用的類別方法和屬性。
    子類別應定義一個名為 `_display_names` 的類別屬性 (字典)，
    用於映射成員值到其對應的中文顯示名稱。
    """

    @classmethod
    def get_by_value(cls: Type[_S], value: str, default: Optional[_S] = None) -> Optional[_S]:
        """
        根據成員的 value (字串值) 安全地獲取 Enum 成員實例。
        如果找不到對應的成員，則回傳 default 值 (預設為 None)。
        cls: Type[_S] - 指示 cls 是 _S 所代表的那個類別 (例如 UserRole)。
        -> Optional[_S] - 回傳 _S 所代表的類別的實例，或者 None。
        """
        try:
            return cls(value)  # cls(value) 是 Enum 從值創建實例的標準方式
        except ValueError:  # 如果 value 無效，Enum 會拋出 ValueError
            return default

    @classmethod
    def get_by_name(cls: Type[_S], name: str, default: Optional[_S] = None) -> Optional[_S]:
        """
        根據成員的 name (即 Enum 的鍵名，如 'ADMIN') 安全地獲取 Enum 成員實例。
        預設會將傳入的 name 轉為大寫進行匹配，因為 Enum 的鍵名通常是大寫的。
        """
        try:
            return cls[name.upper()]  # cls[key_name] 是 Enum 從鍵名獲取實例的標準方式
        except KeyError:  # 如果 key_name 無效，Enum 會拋出 KeyError
            return default

    @classmethod
    def get_values(cls) -> List[str]:
        """獲取所有 Enum 成員的 value (字串值) 列表。"""
        return [member.value for member in cls]

    @classmethod
    def get_names(cls) -> List[str]:
        """獲取所有 Enum 成員的 name (鍵名) 列表。"""
        return [member.name for member in cls]

    @property
    def display_name(self) -> str:
        """
        獲取 Enum 成員實例的顯示名稱 (通常是中文)。
        它會從該 Enum 類別 (透過 type(self) 獲取) 的 `_display_names` 字典中查找。
        如果找不到，則回傳一個根據成員 name 自動產生的、更通用的標題化名稱。
        'self' 代表 Enum 的一個具體實例 (例如 UserRole.ADMIN)。
        """
        return type(self)._display_names.get(self.value, self.name.replace("_", " ").title())

    @classmethod
    def get_choices(cls) -> List[Tuple[str, str]]:
        """
        獲取 (value, display_name) 格式的元組列表，
        常用於網頁表單的選項 (例如 WTForms 的 SelectField)。
        """
        return [(member.value, member.display_name) for member in cls]
