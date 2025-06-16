from datetime import datetime, timezone
from typing import Any, Dict

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship

from ..extensions import db
from .enums import BloodTypeEnum, GenderEnum, GuestRoleEnum, MatchPositionEnum


class Member(db.Model):
    """
    球隊成員模型 - 支援正式會員和訪客系統

    這個模型設計為混合系統，可以同時管理：
    1. 正式會員：有對應的 User 帳號，完整的隊籍管理
    2. 訪客球員：臨時參與比賽的球員，無需註冊帳號

    主要特性：
    - 統一的數據結構，便於統計和管理
    - 靈活的顯示名稱邏輯
    - 支援訪客升級為正式會員
    - 完整的使用記錄追踪

    使用示例：
        # 創建訪客
        guest = Member.create_guest("小王", "0912345678", created_by_user_id=1)

        # 創建正式會員（通常通過 MemberService）
        member = Member(name="小李", user_id=1, is_guest=False)

        # 統一查詢
        active_players = Member.get_active_players(include_guests=True)
    """

    __tablename__ = "members"

    id = db.Column(Integer, primary_key=True, comment="隊員唯一識別碼")

    # --- 基本 Bio 資料 ---
    # 所有球員（正式會員和訪客）都需要的基本資訊
    name = db.Column(String(80), nullable=False, comment="真實姓名")
    student_id = db.Column(
        String(20), unique=True, nullable=True, index=True, comment="學號（僅正式會員）"
    )

    # 生理特徵資訊（主要用於正式會員，訪客通常不填）
    gender = db.Column(
        SQLAlchemyEnum(
            GenderEnum,
            name="gender_enum_members",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=True,
        comment="性別（male/female）",
    )
    blood_type = db.Column(
        SQLAlchemyEnum(
            BloodTypeEnum,
            name="blood_type_enum_members",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=True,
        comment="血型（A/B/AB/O/unknown）",
    )
    position = db.Column(
        SQLAlchemyEnum(
            MatchPositionEnum,
            name="player_position_enum_members",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=True,
        comment="擅長位置（front/back/versatile）",
    )

    # --- 訪客相關欄位 ---
    # 這些欄位用於區分和管理訪客球員
    is_guest = db.Column(
        Boolean, default=False, nullable=False, comment="是否為訪客球員"
    )
    guest_phone = db.Column(
        String(20), nullable=True, comment="訪客電話（用於聯絡和識別）"
    )
    guest_identifier = db.Column(
        String(50), nullable=True, unique=True, comment="訪客唯一識別碼（系統生成）"
    )
    created_by_user_id = db.Column(
        Integer, ForeignKey("users.id"), nullable=True, comment="創建訪客的用戶ID"
    )
    created_at = db.Column(
        DateTime, default=datetime.now(timezone.utc), comment="創建時間"
    )
    last_used_at = db.Column(
        DateTime, nullable=True, comment="最後使用時間（訪客專用）"
    )
    usage_count = db.Column(Integer, default=0, comment="使用次數（訪客專用）")

    # --- 隊籍狀態與日期 ---
    # 用於管理正式會員的隊籍狀態，訪客通常不需要這些資訊
    joined_date = db.Column(Date, nullable=True, comment="入隊日期（正式會員專用）")
    leaved_date = db.Column(Date, nullable=True, comment="離隊日期（若已離隊）")

    # --- TrueSkill 評分系統 ---
    # 所有球員都有評分，用於技能評估和配對
    mu = db.Column(
        Float,
        nullable=False,
        default=25.0,
        comment="TrueSkill μ 值（平均實力，預設25.0）",
    )
    sigma = db.Column(
        Float,
        nullable=False,
        default=(25.0 / 3.0),
        comment="TrueSkill σ 值（實力不確定性，預設8.33）",
    )

    # --- 訪客相關欄位（新增） ---
    guest_role = db.Column(
        SQLAlchemyEnum(
            GuestRoleEnum,
            name="guest_role_enum",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=True,
        comment="訪客在比賽中的身份類型",
    )

    guest_notes = db.Column(
        Text, nullable=True, comment="訪客備註（如：來自哪個學校、特殊說明等）"
    )

    # 備註欄位，可用於記錄特殊資訊
    notes = db.Column(Text, nullable=True, comment="關於此隊員的備註")

    # --- 關聯：所屬組織 ---
    # 正式會員通常屬於某個組織（如學校、俱樂部），訪客可能沒有組織
    organization_id = db.Column(
        Integer,
        ForeignKey("organizations.id", name="fk_members_organization_id"),
        nullable=True,
        index=True,
        comment="所屬組織ID（可選）",
    )
    organization = relationship("Organization", back_populates="members")

    # --- 關聯：使用球拍 ---
    # 記錄球員偏好的球拍型號，用於統計和推薦
    racket_id = db.Column(
        Integer,
        ForeignKey("rackets.id", name="fk_members_racket_id"),
        nullable=True,
        index=True,
        comment="使用球拍ID（可選）",
    )
    racket = relationship("Racket", back_populates="members_using")

    # --- 關聯：對應的使用者帳號 (一對一) ---
    # 關鍵修改：訪客可以沒有對應的 User 帳號
    user_id = db.Column(
        Integer,
        ForeignKey("users.id", name="fk_members_user_id", ondelete="CASCADE"),
        unique=True,
        nullable=True,  # 重要：訪客為 None，正式會員必須有值
        index=True,
        comment="對應的使用者帳號ID（訪客為空）",
    )
    # 明確指定外鍵，避免與 created_by_user_id 衝突
    user = relationship("User", foreign_keys=[user_id], back_populates="member_profile")

    # --- 關聯：創建者 ---
    # 記錄誰創建了這個訪客球員
    creator = relationship("User", foreign_keys=[created_by_user_id])

    # --- 關聯：該隊員的所有比賽統計記錄 ---
    # 用於統計分析和評分計算
    match_stats_records = relationship(
        "PlayerStats",
        back_populates="member",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    # --- 計算屬性 ---
    @property
    def conservative_score(self):
        """
        保守評分 (R_conservative) - 官方排名依據
        公式：μ - k*σ，其中 k 為可配置的保守係數

        這是排行榜的主要排名依據，確保：
        1. 新手因高 σ 而被適當抑制排名
        2. 有經驗球員因低 σ 而獲得應有排名
        3. 系統整體穩定性
        """
        config = self.get_trueskill_config()
        k = config["conservative_k"]
        return self.mu - (k * self.sigma)

    @property
    def official_rank_score(self):
        """
        官方排名分數 - conservative_score 的語義化別名
        這是排行榜應該使用的主要分數
        """
        return self.conservative_score

    @property
    def score(self):
        """
        傳統評分計算，保持向後兼容
        現在直接使用 conservative_score 確保一致性
        """
        return self.conservative_score

    @property
    def potential_skill(self):
        """
        潛在實力 (μ 值) - 系統認知的技術天花板
        不受不確定性影響，反映純粹的技術水平
        """
        return self.mu

    @property
    def consistency_rating(self):
        """
        穩定度評分 - σ 值的反向指標 (0-100分制)

        計算邏輯：
        - σ >= max_sigma (8.33): 0分 (完全不穩定)
        - σ <= min_sigma (1.0): 100分 (非常穩定)
        - 中間值: 線性映射

        應用場景：
        - 判斷球員是否為「神鬼刀」型選手
        - 評估球員經驗豐富程度
        - 種子排位參考
        """
        config = self.get_trueskill_config()
        max_sigma = config["stability_max_sigma"]
        min_sigma = config["stability_min_sigma"]

        if self.sigma >= max_sigma:
            return 0
        elif self.sigma <= min_sigma:
            return 100
        else:
            # 線性映射到 0-100
            normalized = (max_sigma - self.sigma) / (max_sigma - min_sigma)
            return int(100 * normalized)

    @property
    def experience_level(self):
        """
        經驗等級 - 基於 σ 值的分級評估

        Returns:
            str: 經驗等級描述
        """
        sigma = self.sigma
        if sigma >= 7.0:
            return "新手"
        elif sigma >= 5.0:
            return "初級"
        elif sigma >= 3.0:
            return "中級"
        elif sigma >= 2.0:
            return "高級"
        else:
            return "資深"

    @property
    def is_experienced_player(self):
        """
        是否為有經驗的球員
        基於 σ 值判斷，σ 較低表示經驗豐富
        """
        config = self.get_trueskill_config()
        threshold_sigma = config["stability_max_sigma"] * 0.6  # 約 5.0
        return self.sigma < threshold_sigma

    @property
    def rating_confidence(self):
        """
        評分可信度 (0-100分制)
        σ 越低，評分越可信
        """
        config = self.get_trueskill_config()
        max_sigma = config["stability_max_sigma"]

        if self.sigma >= max_sigma:
            return 0
        else:
            # 將 σ 值反向映射到可信度
            confidence = (1 - self.sigma / max_sigma) * 100
            return int(max(0, min(100, confidence)))

    @property
    def display_name(self):
        """
        統一的顯示名稱邏輯（增強版本）

        顯示邏輯優先順序：
        1. 訪客："{name} (身份)" 或 "{name} (身份-{手機尾號})"
        2. 正式會員有 user.display_name：使用 user.display_name
        3. 其他情況：使用 member.name

        Returns:
            str: 適合顯示的名稱
        """
        if self.is_guest:
            # 訪客顯示格式
            role_display = self.get_guest_role_display() or "訪客"
            if self.guest_phone:
                return f"{self.name} ({role_display}-{self.guest_phone[-4:]})"
            return f"{self.name} ({role_display})"
        elif self.user and self.user.display_name:
            # 正式會員優先使用 User 的 display_name
            return self.user.display_name
        else:
            # 備用方案：使用 Member 的 name
            return self.name

    @property
    def is_active(self):
        """
        判斷球員是否為活躍狀態

        這個 property 被 Schema 和統計功能廣泛使用。

        活躍邏輯：
        1. 訪客：未離隊即為活躍
        2. 正式會員：User.is_active=True 且未離隊
        3. 無 User 且非訪客：不活躍

        Returns:
            bool: 是否活躍
        """
        if self.is_guest:
            # 訪客根據最後使用時間和離隊日期判斷
            if self.leaved_date:
                return False  # 已離隊的訪客視為不活躍
            return True  # 其他訪客視為活躍
        elif self.user:
            # 正式會員根據 User.is_active 和離隊日期判斷
            return self.user.is_active and (self.leaved_date is None)
        else:
            # 沒有 User 且不是訪客，視為不活躍
            return False

    @property
    def is_active_player(self):
        """
        判斷是否為活躍球員（用於比賽統計）

        這是 is_active 的別名，提供更語義化的名稱

        Returns:
            bool: 是否為活躍球員
        """
        return self.is_active

    @property
    def player_type(self):
        """
        返回球員類型的中文描述

        Returns:
            str: "訪客" 或 "正式會員"
        """
        return "訪客" if self.is_guest else "正式會員"

    @property
    def short_display_name(self):
        """
        短版顯示名稱，用於排行榜等空間受限的地方

        Returns:
            str: 簡化的顯示名稱
        """
        if self.is_guest:
            return f"{self.name}(訪)"
        elif self.user and self.user.display_name:
            return self.user.display_name
        return self.name

    def get_current_display_name(self):
        """
        獲取當前顯示名稱（方法版本）

        這個方法在 __repr__ 中被使用，提供了與 display_name property 相同的邏輯

        Returns:
            str: 當前的顯示名稱
        """
        return self.display_name

    def update_usage(self):
        """
        更新訪客使用記錄

        每次訪客參與比賽時應該調用此方法來：
        1. 增加使用次數
        2. 更新最後使用時間

        這些資訊用於：
        - 排序建議列表（常用訪客優先）
        - 清理不活躍的訪客
        - 統計分析

        注意：只有訪客才會更新這些記錄
        """
        if self.is_guest:
            self.usage_count += 1
            self.last_used_at = datetime.now(timezone.utc)

    def can_be_deleted(self):
        """
        檢查是否可以被刪除

        球員如果已經參與過比賽，通常不應該被刪除，
        而是應該標記為離隊或不活躍狀態。

        TODO: 實作具體的檢查邏輯
        - 檢查 MatchRecord 中的參與記錄
        - 檢查 PlayerStats 統計記錄
        - 考慮軟刪除策略

        Returns:
            bool: 是否可以安全刪除
        """
        # 這裡需要檢查 MatchRecord 等相關表
        # 暫時簡化邏輯
        return True  # 實際實作時需要檢查比賽記錄

    def promote_to_member(self, user_data: dict):
        """
        將訪客升級為正式會員

        這是一個重要的功能，允許將表現良好的訪客球員
        轉換為正式的隊伍成員。

        升級過程：
        1. 驗證當前是訪客
        2. 創建對應的 User 帳號
        3. 更新 Member 記錄
        4. 保留歷史使用記錄

        Args:
            user_data (dict): 創建 User 所需的資料，包含：
                - username: 手機號碼（必須）
                - email: 電子郵件（可選）
                - display_name: 顯示名稱（可選，預設使用 member.name）
                - password: 密碼（可選）
                - role: 角色（可選，預設 'member'）

        Raises:
            ValueError: 如果不是訪客球員

        Example:
            guest.promote_to_member({
                'username': '0912345678',
                'email': 'test@example.com',
                'password': 'newpassword123'
            })
        """
        if not self.is_guest:
            raise ValueError("只有訪客可以升級為正式會員")

        from .user import User  # 避免循環導入

        # 創建對應的 User 帳號
        new_user = User(
            username=user_data.get("username"),
            email=user_data.get("email"),
            display_name=user_data.get("display_name") or self.name,
            role=user_data.get("role", "member"),
            is_active=True,
        )
        if user_data.get("password"):
            new_user.set_password(user_data["password"])

        # 更新 Member 記錄
        self.is_guest = False
        self.user = new_user
        self.guest_phone = None
        self.guest_identifier = None
        # 保留 created_by_user_id 作為歷史記錄

    def to_dict(
        self,
        four_d_score: bool = True,
        org_detail: bool = True,
        racket_detail: bool = True,
        user_detail: bool = True,
    ) -> Dict[str, Any]:
        """
        將 Member 物件轉換為字典格式

        Args:
            four_d_score: 是否包含四維度評分
            org_detail: 是否包含組織詳細資訊
            racket_detail: 是否包含球拍詳細資訊
            user_detail: 是否包含使用者帳號詳細資訊
        """
        # 原有的基礎資料
        data = {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "short_display_name": self.short_display_name,
            "student_id": self.student_id,
            "gender": self.gender.value if self.gender else None,
            "blood_type": self.blood_type.value if self.blood_type else None,
            "position": self.position.value if self.position else None,
            "is_active": self.is_active,
            "player_type": self.player_type,
            "joined_date": self.joined_date.isoformat() if self.joined_date else None,
            "leaved_date": self.leaved_date.isoformat() if self.leaved_date else None,
            "notes": self.notes,
            "user_id": self.user_id,
            "is_guest": self.is_guest,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

        # 四維度評分系統
        if four_d_score:
            # 主要評分
            data.update(
                {
                    "official_rank_score": round(self.conservative_score, 2),
                    "conservative_score": round(self.conservative_score, 2),
                    "potential_skill": round(self.potential_skill, 2),
                    "consistency_rating": self.consistency_rating,
                    "experience_level": self.experience_level,
                    "rating_confidence": self.rating_confidence,
                    "is_experienced_player": self.is_experienced_player,
                }
            )

            # 原始 TrueSkill 數據
            data.update(
                {
                    "mu": round(self.mu, 3) if self.mu is not None else None,
                    "sigma": round(self.sigma, 3) if self.sigma is not None else None,
                    "score": round(self.score, 2),  # 保持向後兼容
                }
            )

            # 完整四維度數據
            data["four_dimensions"] = self.get_four_dimension_scores()
            data["rating_summary"] = self.get_rating_summary()

        # 訪客相關資料 (保持原有邏輯)
        if self.is_guest:
            guest_data = {
                "guest_phone": self.guest_phone,
                "guest_identifier": self.guest_identifier,
                "usage_count": self.usage_count,
                "last_used_at": self.last_used_at.isoformat()
                if self.last_used_at
                else None,
                "guest_role": self.guest_role.value if self.guest_role else None,
                "guest_role_display": self.get_guest_role_display(),
                "guest_role_description": self.get_guest_role_description(),
                "guest_notes": self.guest_notes,
            }
            data.update(guest_data)

            if user_detail and self.creator:
                data["creator_info"] = {
                    "username": self.creator.username,
                    "display_name": self.creator.display_name,
                }
        elif user_detail and self.user:
            data["user_info"] = {
                "username": self.user.username,
                "user_display_name": self.user.display_name,
                "role": self.user.role.value if self.user.role else None,
                "is_active": self.user.is_active,
            }

        # 組織和球拍資訊 (保持原有邏輯)
        if org_detail and self.organization:
            data["organization_id"] = self.organization_id
            data["organization_name"] = self.organization.name

        if racket_detail and self.racket:
            data["racket_id"] = self.racket_id
            if hasattr(self.racket, "to_dict"):
                data["racket_info"] = self.racket.to_dict()
            else:
                data["racket_info"] = self.racket.name

        return data

    def __repr__(self) -> str:
        """
        提供 Member 物件的字串表示，用於調試和日誌記錄

        格式：<Member id={id}, name='{display_name}'{player_type}{org_info}>

        Examples:
            <Member id=1, name='小王' [訪客] (Org: 台大羽球社)>
            <Member id=2, name='小李' (Org: 清大羽球隊)>

        Returns:
            str: 物件的字串表示
        """
        org_name = (
            self.organization.name
            if self.organization and hasattr(self.organization, "name")
            else None
        )
        org_info = f" (Org: {org_name})" if org_name else ""
        player_type = " [訪客]" if self.is_guest else ""
        return f"<Member id={self.id}, name='{self.get_current_display_name()}'{player_type}{org_info}>"

    def get_four_dimension_scores(self):
        """
        獲取完整的四維度評分

        Returns:
            dict: 包含四個維度評分的字典
        """
        return {
            "official_rank": round(self.conservative_score, 2),
            "potential_skill": round(self.potential_skill, 2),
            "consistency": self.consistency_rating,
            "experience_level": self.experience_level,
            "rating_confidence": self.rating_confidence,
        }

    def get_rating_summary(self):
        """
        獲取評分摘要信息

        Returns:
            dict: 評分摘要
        """
        return {
            "official_score": round(self.conservative_score, 2),
            "raw_mu": round(self.mu, 3),
            "raw_sigma": round(self.sigma, 3),
            "stability_rating": self.consistency_rating,
            "experience_level": self.experience_level,
            "confidence": self.rating_confidence,
            "is_experienced": self.is_experienced_player,
        }

    # --- 比較和排名方法 ---
    def compare_skill_with(self, other_member):
        """
        與另一位球員比較技術水平

        Args:
            other_member: 另一位 Member 實例

        Returns:
            dict: 比較結果
        """
        if not isinstance(other_member, Member):
            raise ValueError("比較對象必須是 Member 實例")

        skill_diff = self.conservative_score - other_member.conservative_score
        confidence_diff = self.rating_confidence - other_member.rating_confidence

        return {
            "skill_advantage": round(skill_diff, 2),
            "confidence_advantage": confidence_diff,
            "is_likely_stronger": skill_diff > 0,
            "comparison_reliability": min(
                self.rating_confidence, other_member.rating_confidence
            ),
        }

    @classmethod
    def get_ranking_by_conservative_score(cls, limit=None, include_guests=True):
        """
        基於保守評分的排行榜查詢

        這是推薦的排行榜生成方法，使用 conservative_score 作為排序依據

        Args:
            limit: 限制返回數量
            include_guests: 是否包含訪客

        Returns:
            Query: 按保守評分排序的查詢對象
        """
        query = cls.get_active_players(include_guests=include_guests)

        # 按保守評分降序排列
        query = query.order_by(
            # 主要排序：保守評分
            (cls.mu - 2.0 * cls.sigma).desc(),
            # 次要排序：穩定度 (σ 越小越前)
            cls.sigma.asc(),
            # 第三排序：潛在技能
            cls.mu.desc(),
        )

        if limit:
            query = query.limit(limit)

        return query

    # --- 類方法（Class Methods）---
    @classmethod
    def create_guest(
        cls,
        name: str,
        phone: str = None,
        created_by_user_id: int = None,
        guest_role: GuestRoleEnum = GuestRoleEnum.NEUTRAL,
        organization_id: int = None,
        notes: str = None,
    ):
        """
        類方法：快速創建訪客球員

        這是創建訪客的推薦方式，會自動處理所有必要的欄位設定。

        Args:
            name (str): 訪客姓名（必須）
            phone (str, optional): 訪客電話
            created_by_user_id (int, optional): 創建者的用戶ID
            guest_role (GuestRoleEnum, optional): 訪客身份類型，預設為 NEUTRAL
            organization_id (int, optional): 所屬組織ID
            notes (str, optional): 備註說明

        Returns:
            Member: 新創建的訪客 Member 實例
        """
        timestamp = int(datetime.now(timezone.utc).timestamp())
        guest_identifier = f"GUEST_{timestamp}_{name[:3].upper()}"

        guest = cls(
            name=name,
            is_guest=True,
            guest_phone=phone,
            guest_identifier=guest_identifier,
            guest_role=guest_role,
            guest_notes=notes,
            created_by_user_id=created_by_user_id,
            organization_id=organization_id,
            user_id=None,
            usage_count=0,
            created_at=datetime.now(timezone.utc),
        )

        return guest

    def get_guest_role_display(self):
        """
        獲取訪客身份的顯示名稱

        Returns:
            str: 訪客身份的中文顯示名稱，如果不是訪客則返回 None
        """
        if self.is_guest and self.guest_role:
            return GuestRoleEnum.get_display_name(self.guest_role)
        return None

    def get_guest_role_description(self):
        """
        獲取訪客身份的描述

        Returns:
            str: 訪客身份的詳細描述，如果不是訪客則返回 None
        """
        if self.is_guest and self.guest_role:
            return GuestRoleEnum.get_description(self.guest_role)
        return None

    def update_guest_info(
        self, name=None, phone=None, guest_role=None, organization_id=None, notes=None
    ):
        """
        更新訪客資訊

        Args:
            name (str, optional): 新的姓名
            phone (str, optional): 新的電話
            guest_role (GuestRoleEnum, optional): 新的身份類型
            organization_id (int, optional): 新的組織ID
            notes (str, optional): 新的備註

        Raises:
            ValueError: 如果不是訪客球員
        """
        if not self.is_guest:
            raise ValueError("只有訪客可以使用此方法更新資訊")

        if name is not None:
            self.name = name
        if phone is not None:
            self.guest_phone = phone
        if guest_role is not None:
            self.guest_role = guest_role
        if organization_id is not None:
            self.organization_id = organization_id
        if notes is not None:
            self.guest_notes = notes

    @classmethod
    def get_active_players(cls, include_guests=True):
        """
        類方法：獲取所有活躍球員的查詢物件

        這個方法提供了一個便利的方式來查詢活躍球員，
        可以根據需要選擇是否包含訪客。

        Args:
            include_guests (bool): 是否包含訪客球員

        Returns:
            Query: SQLAlchemy Query 物件，可以進一步添加過濾條件

        Example:
            # 獲取所有活躍球員（包含訪客）
            all_active = Member.get_active_players(include_guests=True).all()

            # 獲取活躍的正式會員並按分數排序
            members = Member.get_active_players(include_guests=False).order_by(Member.score.desc()).all()
        """
        from .user import User  # 避免循環導入

        if include_guests:
            # 包含訪客和正式會員
            return cls.query.outerjoin(User).filter(
                db.or_(
                    # 訪客條件：is_guest=True 且未離隊
                    db.and_(cls.is_guest == True, cls.leaved_date.is_(None)),
                    # 正式會員條件：有活躍的 User 且未離隊
                    db.and_(
                        cls.is_guest == False,
                        User.is_active == True,
                        cls.leaved_date.is_(None),
                    ),
                )
            )
        else:
            # 只包含正式會員
            return cls.query.join(User).filter(
                cls.is_guest == False, User.is_active == True, cls.leaved_date.is_(None)
            )

    @classmethod
    def search_players(
        cls, query_text: str, include_guests=True, created_by_user_id=None
    ):
        """
        類方法：搜尋球員

        提供全文搜尋功能，支援搜尋姓名、顯示名稱、學號、電話等欄位。

        Args:
            query_text (str): 搜尋關鍵字
            include_guests (bool): 是否包含訪客
            created_by_user_id (int, optional): 如果指定，只搜尋該用戶創建的訪客

        Returns:
            List[Member]: 搜尋結果列表

        Example:
            # 搜尋所有包含"王"的球員
            results = Member.search_players("王", include_guests=True)

            # 搜尋我創建的訪客中包含"小"的
            my_guests = Member.search_players("小", include_guests=True, created_by_user_id=1)
        """
        from .user import User  # 避免循環導入

        search_like = f"%{query_text}%"
        results = []

        # 搜尋正式會員
        members_query = cls.query.join(User).filter(
            cls.is_guest == False,
            User.is_active == True,
            db.or_(
                cls.name.ilike(search_like),
                User.display_name.ilike(search_like),
                User.username.ilike(search_like),
                cls.student_id.ilike(search_like),
            ),
        )
        results.extend(members_query.all())

        # 搜尋訪客（如果允許）
        if include_guests:
            guests_query = cls.query.filter(cls.is_guest == True)

            if created_by_user_id:
                guests_query = guests_query.filter(
                    cls.created_by_user_id == created_by_user_id
                )

            guests_query = guests_query.filter(
                db.or_(
                    cls.name.ilike(search_like),
                    cls.guest_identifier.ilike(search_like),
                    cls.guest_phone.ilike(search_like),
                )
            )
            results.extend(guests_query.all())

        return results
