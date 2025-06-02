from flask import current_app, jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from . import bp
from ..extensions import db
from ..models.enums import UserRoleEnum
from ..models.member import Member
from ..models.organization import Organization
from ..models.user import User
from ..services.member_service import (
    create_member_with_user,
    UserMemberServiceError,
)  # 使用新名稱
from ..tools.validators import (
    validate_username,
    validate_email,
    validate_member_student_id,
    validate_role_str,
    validate_gender_str_for_member,
    validate_position_str_for_member,
    validate_organization_id_for_member,
    validate_member_name,
    validate_display_name,
)


@bp.route("/members", methods=["GET"])
@jwt_required(optional=True)
def get_members_list():
    try:
        # --- 篩選 ---
        query = Member.query.outerjoin(User, Member.user_id == User.id).outerjoin(
            Organization, Member.organization_id == Organization.id
        )

        if request.args.get("all", "false", type=str).lower() != "true":
            query = query.filter(Member.is_active == True)

        if org_id_filter := request.args.get("organization_id", type=int):
            query = query.filter(Member.organization_id == org_id_filter)

        if search_term := request.args.get("name", type=str):
            search_like = f"%{search_term}%"
            query = query.filter(
                or_(
                    Member.name.ilike(search_like),
                    Member.display_name.ilike(search_like),
                    User.username.ilike(search_like),  # 搜尋 User.username (手機號)
                    Member.student_id.ilike(
                        search_like
                    ),  # 搜尋 Member.student_id (學號)
                )
            )

        # --- 排序 ---
        sort_by_field = request.args.get("sort_by", "name", type=str)
        sort_order = request.args.get("sort_order", "asc", type=str).lower()

        sort_attr = None
        if hasattr(Member, sort_by_field):
            sort_attr = getattr(Member, sort_by_field)
        elif hasattr(User, sort_by_field) and sort_by_field in [
            "username",
            "email",
            "role",
        ]:
            sort_attr = getattr(User, sort_by_field)
        elif (
            hasattr(Organization, "name") and sort_by_field == "organization_name"
        ):  # 按組織名排序
            sort_attr = Organization.name

        if sort_attr:
            query = query.order_by(
                sort_attr.desc() if sort_order == "desc" else sort_attr.asc()
            )
        else:
            query = query.order_by(Member.name.asc())

        # --- 分頁 (可選，如果前端不處理) ---
        # page = request.args.get('page', 1, type=int)
        # per_page = request.args.get('per_page', 10, type=int)
        # paginated_members = query.paginate(page=page, per_page=per_page, error_out=False)
        # members = paginated_members.items
        # return jsonify({
        #     "members": [member.to_dict(for_leaderboard=False) for member in members],
        #     "total_pages": paginated_members.pages,
        #     "current_page": paginated_members.page,
        #     "total_items": paginated_members.total
        # })
        members = query.all()
        return jsonify([member.to_dict() for member in members])

    except Exception as e:
        current_app.logger.error(f"Error in get_members_list: {str(e)}", exc_info=True)
        return jsonify({"error": "獲取成員列表時發生錯誤。"}), 500


@bp.route("/members/<int:member_id>", methods=["GET"])
@jwt_required(optional=True)
def get_single_member(member_id):
    member = db.session.get(Member, member_id)
    if not member:
        return jsonify({"error": "找不到指定的成員"}), 404
    return jsonify(member.to_dict())


@bp.route("/members", methods=["POST"])
# @admin_required
def route_create_member():
    data = request.get_json()
    if not data:
        return jsonify({"error": "請求內容必須是 JSON"}), 400
    try:
        new_user, new_member, actual_password_used = create_member_with_user(data)
        db.session.commit()

        response_data = {
            "message": "成員及使用者帳號已成功建立。",
            "member": new_member.to_dict(),
            "user": new_user.to_dict(),  # 通常 User to_dict 不包含 member detail，避免循環
        }
        # 提示初始密碼
        password_info_key = "initial_password_info"
        if not data.get("password") and actual_password_used == new_user.username:
            response_data[password_info_key] = (
                f"使用者初始密碼為其手機號碼 ({new_user.username})，請提醒使用者修改。"
            )
        elif not data.get("password"):
            response_data[password_info_key] = (
                f"使用者初始密碼為系統預設，請提醒使用者修改。"
            )

        return jsonify(response_data), 201

    except UserMemberServiceError as e_service:
        db.session.rollback()
        return jsonify({"message": e_service.args[0], "errors": e_service.errors}), 400
    except Exception as e:  # 其他未預期錯誤
        db.session.rollback()
        current_app.logger.error(
            f"Create member unexpected error: {str(e)}", exc_info=True
        )
        return jsonify({"error": "建立過程中發生未預期錯誤。"}), 500


@bp.route("/members/<int:member_id>", methods=["PUT"])
# @admin_required
def route_update_member(member_id):
    # acting_admin_id = get_jwt_identity() # 暫時移除
    # acting_admin = db.session.get(User, acting_admin_id) # 暫時移除

    member_to_update = db.session.get(Member, member_id)
    if not member_to_update:
        return jsonify({"error": "找不到指定的成員"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "請求內容必須是 JSON"}), 400

    errors = {}
    user_account = member_to_update.user_account

    # --- 1. 更新 Member 的欄位 ---
    if "name" in data:
        err = validate_member_name(data.get("name"))
        if err:
            errors["name"] = err
        else:
            member_to_update.name = data.get("name").strip()

    if "display_name" in data:
        err = validate_display_name(data.get("display_name"))
        if err:
            errors["display_name"] = err
        else:
            member_to_update.display_name = (
                data.get("display_name", "").strip() or member_to_update.name
            )

    if "student_id" in data:
        err = validate_member_student_id(
            data.get("student_id"), existing_member_id=member_id
        )
        if err:
            errors["student_id"] = err
        else:
            member_to_update.student_id = data.get("student_id", "").strip() or None

    if "gender" in data:
        err, enum_val = validate_gender_str_for_member(data.get("gender"))
        if err:
            errors["gender"] = err
        else:
            member_to_update.gender = enum_val

    if "position" in data:
        err, enum_val = validate_position_str_for_member(data.get("position"))
        if err:
            errors["position"] = err
        else:
            member_to_update.position = enum_val

    if "organization_id" in data:
        err, org_id_int = validate_organization_id_for_member(
            data.get("organization_id")
        )
        if err:
            errors["organization_id"] = err
        else:
            member_to_update.organization_id = org_id_int

    # --- 2. 處理 User 帳號 (基於傳入的 'username' 作為手機號碼) ---
    if "username" in data:
        new_username = data.get("username")
        new_username = (
            new_username.strip()
            if isinstance(new_username, str) and new_username.strip()
            else None
        )

        if new_username:
            # 驗證新 username (手機號)
            username_error = validate_username(
                new_username,
                existing_user_id=(user_account.id if user_account else None),
            )
            if username_error:
                errors["username"] = username_error
            else:
                if user_account:  # Member 已有關聯 User
                    if user_account.username != new_username:
                        user_account.username = new_username
                else:  # Member 沒有關聯 User，則創建新 User
                    user_account = User(
                        username=new_username, role=UserRoleEnum.MEMBER
                    )  # 預設角色
                    user_account.set_password(new_username)  # 手機號即密碼
                    member_to_update.user_account = user_account
                    db.session.add(user_account)
        elif user_account:  # 嘗試清空 username，但 User.username 是 NOT NULL
            errors["username"] = "不能清空已設定的登入帳號 (手機號碼)。"

    # --- 3. 處理 User 的 Email 和 Role (如果 user_account 存在或剛被創建) ---
    if user_account:
        if "email" in data:
            email_val = data.get("email")
            email_val = (
                email_val.strip()
                if isinstance(email_val, str) and email_val.strip()
                else None
            )

            email_error = validate_email(email_val, existing_user_id=user_account.id)
            if email_error:
                errors["email"] = email_error
            else:
                user_account.email = email_val

        if "role" in data:
            role_error, role_enum = validate_role_str(data.get("role"))
            if role_error:
                errors["role"] = role_error
            elif role_enum:  # 角色有效
                # acting_user = db.session.get(User, get_jwt_identity()) # 獲取操作者
                # if acting_user.is_admin() or acting_user.role.level > role_enum.level: # 權限檢查
                user_account.role = role_enum
                # else: errors['role'] = "權限不足以設定此角色。"

        if "is_active_user" in data and isinstance(data.get("is_active_user"), bool):
            user_account.is_active = data.get("is_active_user")

    if errors:
        return jsonify({"message": "資料驗證失敗", "errors": errors}), 400

    try:
        db.session.commit()
        return (
            jsonify(
                {
                    "message": "成員資料已成功更新！",
                    "member": member_to_update.to_dict(),
                }
            ),
            200,
        )
    except Exception as e:  # ...
        db.session.rollback()
        current_app.logger.error(
            f"Update member error for ID {member_id}: {str(e)}", exc_info=True
        )
        return jsonify({"error": "更新成員資料時發生伺服器錯誤。"}), 500


@bp.route("/members/<int:member_id>", methods=["DELETE"])
# @admin_required # 暫時移除
def delete_member_route(member_id):
    # ... (與您之前版本類似，但需確保刪除 User 的邏輯)
    # 關鍵是 cascade="all, delete-orphan" 在 User.team_member_profile relationship 上的作用
    # 以及 Member.user_id 的 ondelete='CASCADE' (如果 User 是 Member 的 "父")
    # 或者 Member.user_id 的 ondelete='SET NULL' (如果 User 刪除時，Member 的 user_id 變 NULL)

    # 簡單假設：如果 User.team_member_profile 有 cascade="all, delete-orphan"，
    # 那麼刪除 User 會自動刪除 Member。
    # 如果 Member.user_id 有 ondelete="CASCADE"，那麼 User 刪除時 Member 也會被 DB 層級刪除。
    # 通常，User 是更核心的實體。

    member_to_delete = db.session.get(Member, member_id)
    if not member_to_delete:
        return jsonify({"error": "找不到指定的成員"}), 404

    # 檢查是否有比賽記錄依賴 (需要 MatchRecord 模型)
    # from ..models.match_record import MatchRecord # 假設 MatchRecord 已匯入
    # match_count = MatchRecord.query.filter(
    #     or_(MatchRecord.side_a_player1_id == member_id, MatchRecord.side_a_player2_id == member_id,
    #         MatchRecord.side_b_player1_id == member_id, MatchRecord.side_b_player2_id == member_id)
    # ).count()
    # if match_count > 0:
    #     return jsonify({"error": f"無法刪除：此成員尚有關聯的 {match_count} 場比賽記錄。"}), 409

    user_account_to_delete = member_to_delete.user_account
    try:
        if user_account_to_delete:
            # 刪除 User 會因為 User.team_member_profile 的 cascade 而刪除 Member
            db.session.delete(user_account_to_delete)
        else:  # 如果 Member 沒有 User 帳號，則直接刪除 Member
            db.session.delete(member_to_delete)

        db.session.commit()
        return jsonify({"message": "成員及其關聯帳號（如果存在）已成功刪除。"}), 200
    except IntegrityError as ie:
        db.session.rollback()
        return (
            jsonify(
                {"error": "無法刪除成員，可能因為尚有關聯的其他數據（例如比賽記錄）。"}
            ),
            409,
        )
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "刪除過程中發生未預期錯誤。"}), 500
