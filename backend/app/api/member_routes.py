import datetime

from flask import current_app, jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy.exc import IntegrityError

from . import bp
from ..auth_utils import admin_required
from ..extensions import db
from ..models.enums import GenderEnum, PositionEnum, UserRoleEnum
from ..models.member import Member
from ..services.member_service import create_member


@bp.route("/members", methods=["GET"])
@jwt_required(optional=True)
def get_members_list():  # 此路由與 /api/leaderboard 功能重疊，需釐清用途
    """獲取成員列表，可篩選。與排行榜類似但可能用於不同目的。"""
    # 此處邏輯可以與 get_leaderboard 非常相似，或者更通用
    # 為了範例，我們假設它回傳所有成員（不論是否活躍，除非有參數）
    # 並且可能用於管理介面中的成員列表，而不僅僅是排行榜
    try:
        show_all = request.args.get("all", "false", type=str).lower() == "true"
        query = Member.query
        if not show_all:
            query = query.filter_by(is_active=True)

        members = query.order_by(Member.name).all()
        return jsonify([member.to_dict() for member in members])  # 獲取完整資訊
    except Exception as e:
        current_app.logger.error(f"Error in get_members_list: {str(e)}", exc_info=True)
        return jsonify({"error": "獲取成員列表時發生錯誤。"}), 500


@bp.route("/members", methods=["POST"])
@admin_required  # 只有管理員可以執行這個完整的成員新增
def admin_create_full_member():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request payload must be JSON"}), 400

    # 從 payload 提取所有 User 和 TeamMember 的欄位
    # User fields
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    role_str = data.get("role", "PLAYER")
    is_active_user = data.get("is_active_user", True)

    # TeamMember fields
    name = data.get("name")
    display_name = data.get("display_name")
    student_id = data.get("student_id")
    gender_str = data.get("gender")
    position_str = data.get("position")
    mu_str = data.get("mu")
    sigma_str = data.get("sigma")
    join_date_str = data.get("join_date")
    is_active_member = data.get("is_active_member", True)
    notes = data.get("notes")

    # --- 基本驗證 (您可以做得更詳細) ---
    errors = {}
    if not username:
        errors["username"] = "Username for login is required."
    if not name:
        errors["name"] = "Member's real name is required."

    role_enum = UserRoleEnum.get_by_name(role_str)
    if not role_enum:
        errors["role"] = f"Invalid role: {role_str}."

    gender_enum = GenderEnum.get_by_name(gender_str) if gender_str else None
    if gender_str and not gender_enum:
        errors["gender"] = f"Invalid gender: {gender_str}."

    position_enum = PositionEnum.get_by_name(position_str) if position_str else None
    if position_str and not position_enum:
        errors["position"] = f"Invalid position: {position_str}."

    join_date_obj = None
    if join_date_str:
        try:
            join_date_obj = datetime.datetime.strptime(join_date_str, "%Y-%m-%d").date()
        except ValueError:
            errors["join_date"] = "Invalid date format for join_date."

    mu_val = None
    if mu_str is not None:
        try:
            mu_val = float(mu_str)
        except ValueError:
            errors["mu"] = "Mu must be a number."

    sigma_val = None
    if sigma_str is not None:
        try:
            sigma_val = float(sigma_str)
        except ValueError:
            errors["sigma"] = "Sigma must be a number."

    if errors:
        return jsonify({"message": "Input validation failed", "errors": errors}), 400

    try:
        new_user, new_member, actual_password = create_member(
            username=username,
            name=name,
            password=password,  # 傳給輔助函數，如果為 None，輔助函數會用預設
            # email=email,
            role=role_enum,
            display_name=display_name,
            student_id=student_id,
            gender=gender_enum,
            position=position_enum,
            mu=mu_val,
            sigma=sigma_val,
            join_date=join_date_obj,
            # is_active_user=is_active_user,
            # is_active_member=is_active_member,
            notes=notes,
        )
        db.session.commit()

        return (
            jsonify(
                {
                    "message": "User and TeamMember created successfully by admin.",
                    "user": new_user.to_dict(),
                    "member": new_member.to_dict(),
                    "initial_password_if_default": (
                        actual_password if not password else "Set by admin"
                    ),
                }
            ),
            201,
        )

    except ValueError as ve:
        db.session.rollback()
        return jsonify({"error": str(ve)}), 409
    except IntegrityError as ie:
        db.session.rollback()
        current_app.logger.error(
            f"Admin create member IntegrityError: {str(ie.orig)}", exc_info=True
        )
        return jsonify({"error": "Database integrity error."}), 409
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Admin create member unexpected error: {str(e)}", exc_info=True
        )
        return jsonify({"error": "An unexpected server error occurred."}), 500


@bp.route("/members/<int:member_id>", methods=["DELETE"])
@admin_required
def delete_member_by_admin(member_id):
    member_to_delete = db.session.get(Member, member_id)
    if not member_to_delete:
        return jsonify({"error": "Member not found"}), 404

    user_to_delete = member_to_delete.user_account  # 獲取關聯的 User

    try:
        # 由於 User.team_member_profile 的 cascade="all, delete-orphan"
        # 且 TeamMember.user_id 的 ondelete="CASCADE"
        # 理論上刪除 User 會自動刪除 TeamMember，反之亦然（如果關聯是雙向強依賴）
        # 為了確保乾淨，可以選擇先刪除 User (如果 User 是「主」) 或 TeamMember
        # 這裡我們假設刪除 TeamMember 會因為 User 模型的 cascade 設定而級聯刪除 User
        # 或者，如果 User 是主體，應該透過 User ID 刪除 User，然後 TeamMember 會被級聯刪除。
        # 讓我們明確一點：如果刪除 TeamMember，也刪除其 User 帳號。

        # 注意：如果 MatchRecord 或 PlayerStats 中有外鍵嚴格指向 TeamMember 的 id
        # 並且沒有設定 ON DELETE SET NULL 或 ON DELETE CASCADE，直接刪除 TeamMember 可能會失敗。
        # 您需要先處理這些依賴，或設定資料庫的級聯刪除規則。
        # 為了範例，我們先假設可以直接刪除。

        if user_to_delete:
            # 先解除關聯 (可選，但有時有助於避免某些 cascade 問題)
            # member_to_delete.user_account = None
            # db.session.flush()
            db.session.delete(user_to_delete)  # 刪除 User

        db.session.delete(member_to_delete)  # 刪除 TeamMember

        db.session.commit()
        current_app.logger.info(
            f"Admin deleted TeamMember (ID: {member_id}) and associated User (ID: {user_to_delete.id if user_to_delete else 'N/A'})."
        )
        return (
            jsonify(
                {
                    "message": "Team member and associated user account deleted successfully."
                }
            ),
            200,
        )
        # 或者返回 204 No Content
        # return '', 204

    except IntegrityError as ie:  # 通常是外鍵約束導致無法刪除
        db.session.rollback()
        current_app.logger.error(
            f"Delete member IntegrityError for ID {member_id}: {str(ie.orig)}",
            exc_info=True,
        )
        return (
            jsonify(
                {
                    "error": "Cannot delete member due to existing references (e.g., in match records)."
                }
            ),
            409,
        )
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Delete member unexpected error for ID {member_id}: {str(e)}",
            exc_info=True,
        )
        return jsonify({"error": "An unexpected server error occurred."}), 500
