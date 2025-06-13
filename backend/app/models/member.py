from datetime import datetime
from typing import Dict

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship

from ..extensions import db
from .enums.bio_enums import BloodTypeEnum, GenderEnum
from .enums.match_enums import MatchPositionEnum


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
    is_guest = db.Column(Boolean, default=False, nullable=False, comment="是否為訪客球員")
    guest_phone = db.Column(String(20), nullable=True, comment="訪客電話（用於聯絡和識別）")
    guest_identifier = db.Column(String(50), nullable=True, unique=True, comment="訪客唯一識別碼（系統生成）")
    created_by_user_id = db.Column(Integer, ForeignKey("users.id"), nullable=True, comment="創建訪客的用戶ID")
    created_at = db.Column(DateTime, default=datetime.utcnow, comment="創建時間")
    last_used_at = db.Column(DateTime, nullable=True, comment="最後使用時間（訪客專用）")
    usage_count = db.Column(Integer, default=0, comment="使用次數（訪客專用）")

    # --- 隊籍狀態與日期 ---
    # 用於管理正式會員的隊籍狀態，訪客通常不需要這些資訊
    joined_date = db.Column(Date, nullable=True, comment="入隊日期（正式會員專用）")
    leaved_date = db.Column(Date, nullable=True, comment="離隊日期（若已離隊）")

    # --- TrueSkill 評分系統 ---
    # 所有球員都有評分，用於技能評估和配對
    mu = db.Column(
        Float, nullable=False, default=25.0, comment="TrueSkill μ 值（平均實力，預設25.0）"
    )
    sigma = db.Column(
        Float,
        nullable=False,
        default=(25.0 / 3.0),
        comment="TrueSkill σ 值（實力不確定性，預設8.33）",
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
    def score(self):
        """
        基於 TrueSkill 的保守評分計算

        使用公式：(μ - 3σ) × 100
        這個公式提供了一個保守的技能評估，確保：
        1. 新球員（高 σ）不會被高估
        2. 有經驗球員（低 σ）得到公平評分
        3. 分數範圍適合排行榜顯示

        Returns:
            int: 保守評分（通常在 0-5000 之間）
        """
        return int((self.mu - 3 * self.sigma) * 100)

    @property
    def display_name(self):
        """
        統一的顯示名稱邏輯

        重要：這個 property 不會與 user.display_name 衝突，
        因為它們在不同的命名空間中：
        - Member.display_name（這個 property）
        - Member.user.display_name（透過 relationship 存取的 User 屬性）

        顯示邏輯優先順序：
        1. 訪客："{name} (訪客)" 或 "{name} (訪客-{手機尾號})"
        2. 正式會員有 user.display_name：使用 user.display_name
        3. 其他情況：使用 member.name

        Returns:
            str: 適合顯示的名稱
        """
        if self.is_guest:
            # 訪客顯示格式
            if self.guest_phone:
                return f"{self.name} (訪客-{self.guest_phone[-4:]})"
            return f"{self.name} (訪客)"
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
            self.last_used_at = datetime.utcnow()

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
            username=user_data.get('username'),
            email=user_data.get('email'),
            display_name=user_data.get('display_name') or self.name,
            role=user_data.get('role', 'member'),
            is_active=True
        )
        if user_data.get('password'):
            new_user.set_password(user_data['password'])

        # 更新 Member 記錄
        self.is_guest = False
        self.user = new_user
        self.guest_phone = None
        self.guest_identifier = None
        # 保留 created_by_user_id 作為歷史記錄

    def to_dict(self, org_detail=True, racket_detail=True, user_detail=True) -> Dict:
        """
        將 Member 物件轉換為字典格式

        這個方法用於 API 響應序列化，提供靈活的細節控制選項。
        根據不同的使用場景，可以選擇包含或排除某些關聯資訊。

        Args:
            org_detail (bool): 是否包含組織詳細資訊
            racket_detail (bool): 是否包含球拍詳細資訊
            user_detail (bool): 是否包含使用者帳號詳細資訊

        Returns:
            Dict: 包含 Member 資訊的字典，結構如下：
                {
                    "id": int,
                    "name": str,
                    "display_name": str,
                    "is_guest": bool,
                    "player_type": str,
                    "is_active": bool,
                    ... (其他基本欄位)
                    "organization_name": str (如果 org_detail=True),
                    "racket_info": dict (如果 racket_detail=True),
                    "user_info": dict (如果 user_detail=True),
                    "creator_info": dict (如果是訪客且 user_detail=True)
                }
        """
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
            "mu": round(self.mu, 3) if self.mu is not None else None,
            "sigma": round(self.sigma, 3) if self.sigma is not None else None,
            "score": self.score,
            "notes": self.notes,
            "user_id": self.user_id,

            # 訪客相關資訊（只有訪客才包含這些欄位）
            "is_guest": self.is_guest,
            "guest_phone": self.guest_phone if self.is_guest else None,
            "guest_identifier": self.guest_identifier if self.is_guest else None,
            "usage_count": self.usage_count if self.is_guest else None,
            "last_used_at": self.last_used_at.isoformat() if self.is_guest and self.last_used_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

        # 組織資訊（根據參數決定是否包含）
        if org_detail:
            data["organization_id"] = self.organization_id
            data["organization_name"] = (
                self.organization.name
                if self.organization and hasattr(self.organization, "name")
                else None
            )

        # 球拍資訊（根據參數決定是否包含）
        if racket_detail:
            data["racket_id"] = self.racket_id
            data["racket_info"] = (
                self.racket.to_dict()
                if self.racket and hasattr(self.racket, "to_dict")
                else (
                    self.racket.name
                    if self.racket and hasattr(self.racket, "name")
                    else None
                )
            )

        # 使用者帳號資訊（根據參數和球員類型決定是否包含）
        if user_detail and self.user:
            # 正式會員的 User 資訊
            data["user_info"] = {
                "username": self.user.username,
                "user_display_name": self.user.display_name,
                "role": self.user.role.value if self.user.role else None,
                "is_active": self.user.is_active,
            }
        elif user_detail and self.is_guest and self.creator:
            # 訪客顯示創建者資訊
            data["creator_info"] = {
                "username": self.creator.username,
                "display_name": self.creator.display_name,
            }

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
        return (
            f"<Member id={self.id}, name='{self.get_current_display_name()}'{player_type}{org_info}>"
        )

    # --- 類方法（Class Methods）---
    @classmethod
    def create_guest(cls, name: str, phone: str = None, created_by_user_id: int = None):
        """
        類方法：快速創建訪客球員

        這是創建訪客的推薦方式，會自動處理所有必要的欄位設定。

        Args:
            name (str): 訪客姓名（必須）
            phone (str, optional): 訪客電話
            created_by_user_id (int, optional): 創建者的用戶ID

        Returns:
            Member: 新創建的訪客 Member 實例（尚未存儲到資料庫）

        Example:
            guest = Member.create_guest("臨時球員", "0912345678", created_by_user_id=1)
            db.session.add(guest)
            db.session.commit()
        """
        timestamp = int(datetime.utcnow().timestamp())
        guest_identifier = f"GUEST_{timestamp}_{name[:3].upper()}"

        guest = cls(
            name=name,
            is_guest=True,
            guest_phone=phone,
            guest_identifier=guest_identifier,
            created_by_user_id=created_by_user_id,
            user_id=None,  # 訪客沒有對應的 User
            usage_count=0,
            created_at=datetime.utcnow()
        )

        return guest

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
                        cls.leaved_date.is_(None)
                    )
                )
            )
        else:
            # 只包含正式會員
            return cls.query.join(User).filter(
                cls.is_guest == False,
                User.is_active == True,
                cls.leaved_date.is_(None)
            )

    @classmethod
    def search_players(cls, query_text: str, include_guests=True, created_by_user_id=None):
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
                cls.student_id.ilike(search_like)
            )
        )
        results.extend(members_query.all())

        # 搜尋訪客（如果允許）
        if include_guests:
            guests_query = cls.query.filter(cls.is_guest == True)

            if created_by_user_id:
                guests_query = guests_query.filter(cls.created_by_user_id == created_by_user_id)

            guests_query = guests_query.filter(
                db.or_(
                    cls.name.ilike(search_like),
                    cls.guest_identifier.ilike(search_like),
                    cls.guest_phone.ilike(search_like)
                )
            )
            results.extend(guests_query.all())

        return results
