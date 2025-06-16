from datetime import datetime, timezone
from typing import Any, Dict

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship

from ..config import RatingCalculationConfig
from ..extensions import db
from .enums import BloodTypeEnum, GenderEnum, GuestRoleEnum, MatchPositionEnum


class Member(db.Model):
    """
    球隊成員模型 - 支援正式會員和訪客系統，整合 TrueSkill 四維度評分

    這個模型設計為混合系統，可以同時管理：
    1. 正式會員：有對應的 User 帳號，完整的隊籍管理
    2. 訪客球員：臨時參與比賽的球員，無需註冊帳號

    主要特性：
    - 統一的數據結構，便於統計和管理
    - TrueSkill 四維度評分系統
    - 靈活的顯示名稱邏輯
    - 支援訪客升級為正式會員
    - 完整的使用記錄追踪

    四維度評分：
    1. 官方排名分數 (official_rank_score): μ - k*σ 的保守評分
    2. 潛在實力 (potential_skill): μ 值，技術天花板
    3. 穩定度評分 (consistency_rating): 基於 σ 的穩定性指標
    4. 經驗等級 (experience_level): 基於 σ 的經驗分級
    """

    __tablename__ = "members"

    # ===== 主鍵 =====
    id = db.Column(Integer, primary_key=True, comment="隊員唯一識別碼")

    # ===== 基本資料 =====
    name = db.Column(String(80), nullable=False, comment="真實姓名")
    student_id = db.Column(
        String(20), unique=True, nullable=True, index=True, comment="學號（僅正式會員）"
    )

    # ===== 生理特徵 =====
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

    # ===== 訪客系統 =====
    is_guest = db.Column(
        Boolean, default=False, nullable=False, comment="是否為訪客球員"
    )
    guest_phone = db.Column(String(20), nullable=True, comment="訪客電話")
    guest_identifier = db.Column(
        String(50), nullable=True, unique=True, comment="訪客唯一識別碼"
    )
    guest_role = db.Column(
        SQLAlchemyEnum(
            GuestRoleEnum,
            name="guest_role_enum",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=True,
        comment="訪客身份類型",
    )
    guest_notes = db.Column(Text, nullable=True, comment="訪客備註")
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

    # ===== 隊籍管理 =====
    joined_date = db.Column(Date, nullable=True, comment="入隊日期")
    leaved_date = db.Column(Date, nullable=True, comment="離隊日期")

    # ===== TrueSkill 評分系統 =====
    mu = db.Column(Float, nullable=False, default=25.0, comment="TrueSkill μ 值")
    sigma = db.Column(
        Float, nullable=False, default=(25.0 / 3.0), comment="TrueSkill σ 值"
    )

    # ===== 備註 =====
    notes = db.Column(Text, nullable=True, comment="隊員備註")

    # ===== 關聯關係 =====
    organization_id = db.Column(
        Integer,
        ForeignKey("organizations.id", name="fk_members_organization_id"),
        nullable=True,
        index=True,
        comment="所屬組織ID",
    )
    organization = relationship("Organization", back_populates="members")

    racket_id = db.Column(
        Integer,
        ForeignKey("rackets.id", name="fk_members_racket_id"),
        nullable=True,
        index=True,
        comment="使用球拍ID",
    )
    racket = relationship("Racket", back_populates="members_using")

    user_id = db.Column(
        Integer,
        ForeignKey("users.id", name="fk_members_user_id", ondelete="CASCADE"),
        unique=True,
        nullable=True,
        index=True,
        comment="對應的使用者帳號ID",
    )
    user = relationship("User", foreign_keys=[user_id], back_populates="member_profile")
    creator = relationship("User", foreign_keys=[created_by_user_id])

    match_stats_records = relationship(
        "PlayerStats",
        back_populates="member",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    # ===== 配置方法 =====
    @classmethod
    def get_trueskill_config(cls):
        """獲取 TrueSkill 評分系統配置參數"""
        return {
            "conservative_k": RatingCalculationConfig.TRUESKILL_CONSERVATIVE_K,
            "stability_max_sigma": RatingCalculationConfig.TRUESKILL_MAX_SIGMA,
            "stability_min_sigma": RatingCalculationConfig.TRUESKILL_MIN_SIGMA,
            "experience_threshold": RatingCalculationConfig.TRUESKILL_EXP_THRESHOLD,
        }

    # ===== 核心評分屬性（四維度評分系統）=====
    @property
    def conservative_score(self):
        """
        保守評分 (R_conservative) - 官方排名依據
        公式：μ - k*σ，解決新手評分虛高問題
        """
        k = self.get_trueskill_config()["conservative_k"]
        return self.mu - (k * self.sigma)

    @property
    def official_rank_score(self):
        """官方排名分數 - 排行榜主要依據"""
        return self.conservative_score

    @property
    def potential_skill(self):
        """潛在實力 (μ 值) - 技術天花板"""
        return self.mu

    @property
    def consistency_rating(self):
        """
        穩定度評分 (0-100分制)
        σ 越低，穩定度越高
        """
        config = self.get_trueskill_config()
        max_sigma = config["stability_max_sigma"]
        min_sigma = config["stability_min_sigma"]

        if self.sigma >= max_sigma:
            return 0
        elif self.sigma <= min_sigma:
            return 100
        else:
            normalized = (max_sigma - self.sigma) / (max_sigma - min_sigma)
            return int(100 * normalized)

    @property
    def experience_level(self):
        """經驗等級 - 基於 σ 值的分級"""
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
    def rating_confidence(self):
        """評分可信度 (0-100分制)"""
        max_sigma = self.get_trueskill_config()["stability_max_sigma"]
        if self.sigma >= max_sigma:
            return 0
        confidence = (1 - self.sigma / max_sigma) * 100
        return int(max(0, min(100, confidence)))

    @property
    def is_experienced_player(self):
        """是否為有經驗的球員"""
        threshold = self.get_trueskill_config()["stability_max_sigma"] * 0.6
        return self.sigma < threshold

    # ===== 向後兼容屬性 =====
    @property
    def score(self):
        """傳統評分，保持向後兼容"""
        return self.conservative_score

    # ===== 顯示和狀態屬性 =====
    @property
    def display_name(self):
        """統一的顯示名稱邏輯"""
        if self.is_guest:
            role_display = self.get_guest_role_display() or "訪客"
            if self.guest_phone:
                return f"{self.name} ({role_display}-{self.guest_phone[-4:]})"
            return f"{self.name} ({role_display})"
        elif self.user and self.user.display_name:
            return self.user.display_name
        else:
            return self.name

    @property
    def short_display_name(self):
        """短版顯示名稱"""
        if self.is_guest:
            return f"{self.name}(訪)"
        elif self.user and self.user.display_name:
            return self.user.display_name
        return self.name

    @property
    def is_active(self):
        """判斷球員是否為活躍狀態"""
        if self.is_guest:
            return self.leaved_date is None
        elif self.user:
            return self.user.is_active and (self.leaved_date is None)
        else:
            return False

    @property
    def is_active_player(self):
        """是否為活躍球員（語義化別名）"""
        return self.is_active

    @property
    def player_type(self):
        """球員類型的中文描述"""
        return "訪客" if self.is_guest else "正式會員"

    # ===== 四維度評分相關方法 =====
    def get_four_dimension_scores(self):
        """獲取完整的四維度評分"""
        return {
            "official_rank": round(self.conservative_score, 2),
            "potential_skill": round(self.potential_skill, 2),
            "consistency": self.consistency_rating,
            "experience_level": self.experience_level,
            "rating_confidence": self.rating_confidence,
        }

    def get_rating_summary(self):
        """獲取評分摘要信息"""
        return {
            "official_score": round(self.conservative_score, 2),
            "raw_mu": round(self.mu, 3),
            "raw_sigma": round(self.sigma, 3),
            "stability_rating": self.consistency_rating,
            "experience_level": self.experience_level,
            "confidence": self.rating_confidence,
            "is_experienced": self.is_experienced_player,
        }

    def compare_skill_with(self, other_member):
        """與另一位球員比較技術水平"""
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

    # ===== 訪客相關方法 =====
    def get_guest_role_display(self):
        """獲取訪客身份的顯示名稱"""
        if self.is_guest and self.guest_role:
            return GuestRoleEnum.get_display_name(self.guest_role)
        return None

    def get_guest_role_description(self):
        """獲取訪客身份的描述"""
        if self.is_guest and self.guest_role:
            return GuestRoleEnum.get_description(self.guest_role)
        return None

    def update_guest_info(
        self, name=None, phone=None, guest_role=None, organization_id=None, notes=None
    ):
        """更新訪客資訊"""
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

    def update_usage(self):
        """更新訪客使用記錄"""
        if self.is_guest:
            self.usage_count += 1
            self.last_used_at = datetime.now(timezone.utc)

    def promote_to_member(self, user_data: dict):
        """將訪客升級為正式會員"""
        if not self.is_guest:
            raise ValueError("只有訪客可以升級為正式會員")

        from .user import User  # 避免循環導入

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

    # ===== 實例方法 =====
    def get_current_display_name(self):
        """獲取當前顯示名稱（方法版本）"""
        return self.display_name

    def can_be_deleted(self):
        """檢查是否可以被刪除"""
        # TODO: 實作具體的檢查邏輯
        return True

    # ===== 序列化方法 =====
    def to_dict(
        self,
        include_four_dimensions: bool = True,
        org_detail: bool = True,
        racket_detail: bool = True,
        user_detail: bool = True,
    ) -> Dict[str, Any]:
        """將 Member 物件轉換為字典格式"""
        # 基礎資料
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
        if include_four_dimensions:
            data.update(
                {
                    "official_rank_score": round(self.conservative_score, 2),
                    "conservative_score": round(self.conservative_score, 2),
                    "potential_skill": round(self.potential_skill, 2),
                    "consistency_rating": self.consistency_rating,
                    "experience_level": self.experience_level,
                    "rating_confidence": self.rating_confidence,
                    "is_experienced_player": self.is_experienced_player,
                    "mu": round(self.mu, 3) if self.mu is not None else None,
                    "sigma": round(self.sigma, 3) if self.sigma is not None else None,
                    "score": round(self.score, 2),  # 向後兼容
                    "four_dimensions": self.get_four_dimension_scores(),
                    "rating_summary": self.get_rating_summary(),
                }
            )

        # 訪客相關資料
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

        # 關聯資訊
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

    # ===== 類方法 =====
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
        """快速創建訪客球員"""
        timestamp = int(datetime.now(timezone.utc).timestamp())
        guest_identifier = f"GUEST_{timestamp}_{name[:3].upper()}"

        return cls(
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

    @classmethod
    def get_active_players(cls, include_guests=True):
        """
        類方法：獲取所有活躍球員的查詢物件
        """
        from .user import User

        if include_guests:
            # 包含訪客和正式會員
            return cls.query.outerjoin(User, cls.user_id == User.id).filter(
                db.or_(
                    db.and_(cls.is_guest == True, cls.leaved_date.is_(None)),
                    db.and_(
                        cls.is_guest == False,
                        User.is_active == True,
                        cls.leaved_date.is_(None),
                    ),
                )
            )
        else:
            # 只包含正式會員
            return cls.query.join(User, cls.user_id == User.id).filter(
                cls.is_guest == False, User.is_active == True, cls.leaved_date.is_(None)
            )

    @classmethod
    def get_ranking_by_conservative_score(cls, limit=None, include_guests=True):
        """
        基於保守評分的排行榜查詢
        """
        query = cls.get_active_players(include_guests=include_guests)

        # 按保守評分降序排列
        query = query.order_by(
            # 主要排序：保守評分
            (
                cls.mu - RatingCalculationConfig.TRUESKILL_CONSERVATIVE_K * cls.sigma
            ).desc(),
            # 次要排序：穩定度 (σ 越小越前)
            cls.sigma.asc(),
            # 第三排序：潛在技能
            cls.mu.desc(),
        )

        if limit:
            query = query.limit(limit)

        return query

    @classmethod
    def search_players(
        cls, query_text: str, include_guests=True, created_by_user_id=None
    ):
        """
        類方法：搜尋球員
        """
        from .user import User

        search_like = f"%{query_text}%"
        results = []

        # 搜尋正式會員
        members_query = cls.query.join(User, cls.user_id == User.id).filter(
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

        # 搜尋訪客
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

    # ===== 特殊方法 =====
    def __repr__(self) -> str:
        """物件的字串表示"""
        org_name = (
            self.organization.name
            if self.organization and hasattr(self.organization, "name")
            else None
        )
        org_info = f" (Org: {org_name})" if org_name else ""
        player_type = " [訪客]" if self.is_guest else ""
        return f"<Member id={self.id}, name='{self.get_current_display_name()}'{player_type}{org_info}>"
