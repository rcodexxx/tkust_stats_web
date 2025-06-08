# your_project/app/services/member_service.py
from flask import current_app
from flask_jwt_extended import create_access_token, create_refresh_token
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from ..extensions import db
from ..models import User, Member, MatchRecord
from ..models.enums import UserRoleEnum, MatchOutcomeEnum
from ..tools.exceptions import UserAlreadyExistsError, AppException, UserNotFoundError


class MemberService:

    @staticmethod
    def _get_leaderboard_data():
        """
        一個高效的內部方法，用於計算並返回排行榜數據。
        """
        current_app.logger.info("--- [Leaderboard] 正在計算排行榜數據 ---")

        # 1. 查詢所有比賽記錄
        all_records = MatchRecord.query.all()
        current_app.logger.info(f"[Leaderboard] 找到 {len(all_records)} 筆總比賽記錄。")

        # 2. 計算每個球員的勝敗場次
        stats = {}
        for record in all_records:
            if record.side_a_outcome == MatchOutcomeEnum.WIN:
                winner_ids, loser_ids = [record.player1_id, record.player2_id], [record.player3_id, record.player4_id]
            elif record.side_a_outcome == MatchOutcomeEnum.LOSS:
                winner_ids, loser_ids = [record.player3_id, record.player4_id], [record.player1_id, record.player2_id]
            else:
                continue

            for p_id in winner_ids:
                if p_id:
                    stats.setdefault(p_id, {"wins": 0, "losses": 0})["wins"] += 1
            for p_id in loser_ids:
                if p_id:
                    stats.setdefault(p_id, {"wins": 0, "losses": 0})["losses"] += 1

        current_app.logger.info(f"[Leaderboard] 計算出的球員統計: {stats}")

        # 3. 獲取所有有比賽記錄且為現役的成員
        player_ids_with_matches = list(stats.keys())
        if not player_ids_with_matches:
            current_app.logger.warning("[Leaderboard] 沒有任何球員有比賽記錄，返回空列表。")
            return []

        query = (
            Member.query.filter(Member.id.in_(player_ids_with_matches))
            .join(Member.user)
            .filter(User.is_active == True)
            .options(joinedload(Member.organization))
        )
        members_for_leaderboard = query.all()
        current_app.logger.info(f"[Leaderboard] 查詢到 {len(members_for_leaderboard)} 位符合條件的現役成員。")

        # 4. 將統計數據附加到成員物件上
        for member in members_for_leaderboard:
            member_stats = stats.get(member.id, {"wins": 0, "losses": 0})
            member.wins = member_stats["wins"]
            member.losses = member_stats["losses"]
            member.total_matches = member.wins + member.losses
            member.win_rate = round((member.wins / member.total_matches) * 100, 2) if member.total_matches > 0 else 0
            current_app.logger.info(f"[Leaderboard] 處理成員 ID {member.id}: 勝={member.wins}, 敗={member.losses}")

        # 5. 排序並返回
        members_for_leaderboard.sort(key=lambda m: m.score, reverse=True)
        current_app.logger.info("--- [Leaderboard] 排行榜數據計算完成 ---")
        return members_for_leaderboard

    @staticmethod
    def get_all_members(args: dict):
        """
        獲取成員列表。如果 'view' 參數為 'leaderboard'，則返回排行榜數據。
        """
        if args.get("view") == "leaderboard":
            return MemberService._get_leaderboard_data()

        # --- 以下為標準的成員列表查詢邏輯 ---
        query = Member.query.options(joinedload(Member.user), joinedload(Member.organization))

        if args.get("all", "false").lower() != "true":
            query = query.join(Member.user).filter(User.is_active == True)

        if search_term := args.get("name"):
            search_like = f"%{search_term}%"
            query = query.join(Member.user, isouter=True).filter(
                or_(
                    Member.name.ilike(search_like),
                    User.display_name.ilike(search_like),
                    User.username.ilike(search_like),
                    Member.student_id.ilike(search_like),
                )
            )

        sort_by = args.get("sort_by", "name")
        sort_order = args.get("sort_order", "asc")
        sort_attr = getattr(Member, sort_by, Member.name)
        query = query.order_by(sort_attr.desc() if sort_order == "desc" else sort_attr.asc())

        return query.all()

    @staticmethod
    def get_member_by_id(member_id: int):
        """Finds a member by their ID, and preloads related user info."""
        return Member.query.options(db.joinedload(Member.user)).get(member_id)

    @staticmethod
    def register_and_login(username: str) -> dict:
        """
        專門用於公開的快速註冊，並在成功後立即登入。
        僅根據手機號碼 (作為 username) 創建 Member 和關聯的 User。
        """
        if User.query.filter_by(username=username).first():
            raise UserAlreadyExistsError(f"手機號碼 '{username}' 已被註冊。")

        default_name = f"隊員_{username[-4:]}"
        initial_password = username

        try:
            # 創建 User 物件
            new_user = User(
                username=username, email=None, role=UserRoleEnum.MEMBER, display_name=default_name, is_active=True
            )
            new_user.set_password(initial_password)
            db.session.add(new_user)

            # 創建 Member 物件並關聯
            new_member = Member(user=new_user, name=default_name)
            db.session.add(new_member)
            db.session.commit()

            # --- 核心改動：註冊成功後，立即生成 Tokens ---
            access_token = create_access_token(identity=str(new_user.id))
            refresh_token = create_refresh_token(identity=str(new_user.id))

            return {
                "user": new_user,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "initial_password_warning": f"註冊成功並已自動登入！您的初始密碼與手機號碼相同 ({initial_password})，請盡快修改密碼。",
            }

        except Exception as e:
            db.session.rollback()
            raise AppException("註冊過程中發生未預期錯誤。")

    @staticmethod
    def create_member_and_user(data: dict) -> Member:
        """
        創建一個新的 Member 及其關聯的 User 帳號。
        'data' 是經過 MemberCreateSchema 驗證後的數據。
        """
        username = data.get("username")
        email = data.get("email")

        # 業務邏輯：檢查 User 是否已存在
        if User.query.filter_by(username=username).first():
            raise UserAlreadyExistsError(f"手機號碼 '{username}' 已被註冊。")
        if email and User.query.filter_by(email=email).first():
            raise UserAlreadyExistsError(f"Email '{email}' 已被註冊。")

        try:
            # 1. 創建 User 物件
            new_user = User(
                username=username,
                email=email,
                role=data.get("role", UserRoleEnum.MEMBER),
                display_name=data.get("display_name") or data.get("name"),
                is_active=data.get("is_active", True),
            )
            # 如果沒有提供密碼，預設使用手機號碼
            new_user.set_password(data.get("password") or username)
            db.session.add(new_user)

            # 2. 創建 Member 物件並關聯
            new_member = Member(
                user=new_user,  # SQLAlchemy 會自動處理 user_id
                name=data["name"],
                student_id=data.get("student_id"),
                gender=data.get("gender"),
                position=data.get("position"),
                organization_id=data.get("organization_id"),
                joined_date=data.get("joined_date"),
                notes=data.get("notes"),
            )
            db.session.add(new_member)
            db.session.commit()
            return new_member
        except IntegrityError as e:
            db.session.rollback()
            raise AppException(f"資料庫錯誤，無法創建成員: {e.orig}", status_code=409)
        except Exception as e:
            db.session.rollback()
            raise AppException(f"創建成員時發生未預期錯誤: {e}")

    @staticmethod
    def update_member(member: Member, data: dict) -> Member:
        """
        Updates an existing member's profile and associated user info.
        'member' is the Member model instance to update.
        'data' is validated data from the MemberUpdateSchema.
        """
        # --- 1. 更新 Member 模型的欄位 ---
        member_fields = [
            "name",
            "student_id",
            "gender",
            "position",
            "organization_id",
            "joined_date",
            "leaved_date",
            "notes",
        ]
        for field in member_fields:
            if field in data:
                setattr(member, field, data[field])

        # --- 2. 更新關聯的 User 模型欄位 ---
        if member.user:
            user_to_update = member.user
            user_fields = ["username", "email", "display_name", "role", "is_active"]

            # 處理唯一性檢查
            if "username" in data and data["username"] != user_to_update.username:
                if User.query.filter(User.username == data["username"], User.id != user_to_update.id).first():
                    raise UserAlreadyExistsError(f"手機號碼 '{data['username']}' 已被其他帳號使用。")

            if "email" in data and data["email"] != user_to_update.email:
                if (
                    data["email"]
                    and User.query.filter(User.email == data["email"], User.id != user_to_update.id).first()
                ):
                    raise UserAlreadyExistsError(f"電子郵件 '{data['email']}' 已被其他帳號使用。")

            # 更新欄位值
            for field in user_fields:
                if field in data:
                    setattr(user_to_update, field, data[field])
        else:
            # 如果 Member 沒有關聯的 User，但 payload 中有 user 相關欄位，可以選擇報錯或忽略
            # 這裡我們選擇忽略，因為管理員的主要目標是更新 Member
            pass

        try:
            db.session.commit()
            return member
        except IntegrityError as e:
            db.session.rollback()
            raise AppException(f"資料庫錯誤，無法更新成員: {e.orig}", status_code=409)
        except Exception as e:
            db.session.rollback()
            raise AppException(f"更新成員時發生未預期錯誤: {e}")

    @staticmethod
    def delete_member(member: Member):
        """
        Deletes a member and their associated user account.
        """
        if not member:
            raise UserNotFoundError("找不到指定的成員。")

        try:
            # The cascade setting on the User->Member relationship should handle this
            db.session.delete(member)
            if member.user:
                db.session.delete(member.user)  # Ensure user is also deleted
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise AppException(f"刪除成員時發生錯誤: {e}")
