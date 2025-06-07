# your_project/app/services/member_service.py
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from ..extensions import db
from ..models import User, Member, MatchRecord
from ..models.enums.match_enums import MatchOutcomeEnum
from ..models.enums.user_enums import UserRoleEnum
from ..tools.exceptions import UserAlreadyExistsError, ValidationError, AppException, UserNotFoundError


class MemberService:

    @staticmethod
    def _get_leaderboard_data():
        """
        一個高效的內部方法，用於計算並返回排行榜數據。
        此方法取代了原先在路由中 N+1 查詢的邏輯。
        """
        # 1. 一次性查詢所有已完成的比賽記錄
        all_records = MatchRecord.query.all()

        # 2. 在記憶體中計算每個球員的勝敗場次
        stats = {}  # key: member_id, value: {'wins': x, 'losses': y}
        for record in all_records:
            if record.side_a_outcome == MatchOutcomeEnum.WIN:
                winner_ids = [record.side_a_player1_id, record.side_a_player2_id]
                loser_ids = [record.side_b_player1_id, record.side_b_player2_id]
            elif record.side_a_outcome == MatchOutcomeEnum.LOSS:
                winner_ids = [record.side_b_player1_id, record.side_b_player2_id]
                loser_ids = [record.side_a_player1_id, record.side_a_player2_id]
            else:  # 平局或未定義結果，跳過
                continue

            for p_id in winner_ids:
                if p_id:
                    stats.setdefault(p_id, {"wins": 0, "losses": 0})["wins"] += 1
            for p_id in loser_ids:
                if p_id:
                    stats.setdefault(p_id, {"wins": 0, "losses": 0})["losses"] += 1

        # 3. 獲取所有現役隊員
        active_members = Member.query.options(joinedload(Member.user_profile), joinedload(Member.organization)).all()

        leaderboard_members = []
        for member in active_members:
            member_stats = stats.get(member.id, {"wins": 0, "losses": 0})
            total_matches = member_stats["wins"] + member_stats["losses"]

            # 只有參與過比賽的成員才加入排行榜
            if total_matches > 0:
                # 動態地將統計數據附加到 member 物件上，以便 Schema 序列化
                member.wins = member_stats["wins"]
                member.losses = member_stats["losses"]
                member.total_matches = total_matches
                member.win_rate = round((member.wins / total_matches) * 100, 2) if total_matches > 0 else 0
                leaderboard_members.append(member)

        # 4. 在 Python 中根據計算後的 'score' 屬性進行最終排序
        leaderboard_members.sort(key=lambda m: m.score, reverse=True)

        return leaderboard_members

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
            query = query.filter(Member.is_active == True)
        # ... 其他篩選和排序邏輯 ...
        if search_term := args.get("name"):
            search_like = f"%{search_term}%"
            query = query.filter(or_(Member.name.ilike(search_like), User.username.ilike(search_like)))

        sort_by = args.get("sort_by", "name")
        sort_order = args.get("sort_order", "asc")
        sort_attr = getattr(Member, sort_by, Member.name)
        query = query.order_by(sort_attr.desc() if sort_order == "desc" else sort_attr.asc())

        return query.all()

    @staticmethod
    def get_member_by_id(member_id: int):
        """Finds a member by their ID."""
        return db.session.get(Member, member_id)

    @staticmethod
    def create_member_and_user(data: dict):
        """
        Creates a new member and an associated user account.
        'data' is validated data from the MemberSchema.
        """
        username = data.get("username")
        email = data.get("email")
        password = data.get("password")

        if not username:
            raise ValidationError({"username": ["必須提供手機號碼作為登入帳號。"]})
        if User.query.filter_by(username=username).first():
            raise UserAlreadyExistsError(f"手機號碼 '{username}' 已被註冊。")
        if email and User.query.filter_by(email=email).first():
            raise UserAlreadyExistsError(f"Email '{email}' 已被註冊。")

        try:
            new_user = User(
                username=username,
                email=email,
                role=UserRoleEnum.MEMBER,
                display_name=data.get("display_name") or data.get("name"),
            )
            new_user.set_password(password or username)  # Fallback to username as password if not provided
            db.session.add(new_user)

            new_member = Member(
                user=new_user,
                name=data["name"],
                display_name=data.get("display_name"),
                student_id=data.get("student_id"),
                gender=data.get("gender"),
                position=data.get("position"),
                organization_id=data.get("organization_id"),
                is_active=data.get("is_active", True),
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
    def update_member(member: Member, data: dict):
        """
        Updates an existing member's profile and associated user info.
        'member' is the Member model instance to update.
        'data' is validated data from the MemberSchema.
        """
        for field, value in data.items():
            if hasattr(member, field):
                setattr(member, field, value)

        # Handle associated User updates
        if member.user:
            if "email" in data and member.user.email != data["email"]:
                if User.query.filter(User.email == data["email"], User.id != member.user.id).first():
                    raise UserAlreadyExistsError(f"Email '{data['email']}' 已被其他帳號使用。")
                member.user.email = data["email"]

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
