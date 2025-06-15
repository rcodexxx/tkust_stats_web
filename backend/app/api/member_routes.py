# backend/app/api/member_routes.py
from flask import current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from marshmallow import ValidationError as MarshmallowValidationError
from sqlalchemy.orm import joinedload

from ..extensions import db
from ..models import Member, Organization
from ..models.enums import GuestRoleEnum
from ..schemas.member_schemas import (
    GuestCreateResponseSchema,
    GuestCreateSchema,
    GuestListResponseSchema,
    GuestQuerySchema,
    GuestRoleOptionSchema,
    GuestUpdateSchema,
    LeaderboardMemberSchema,
    MemberCreateSchema,
    MemberSchema,
    MemberUpdateSchema,
)
from ..services.member_service import MemberService
from ..tools.exceptions import AppException, UserAlreadyExistsError
from . import api_bp

# Instantiate all necessary schemas
member_display_schema = MemberSchema()
members_display_schema = MemberSchema(many=True)
leaderboard_members_schema = LeaderboardMemberSchema(many=True)
member_create_schema = MemberCreateSchema()
member_update_schema = MemberUpdateSchema()

guest_create_schema = GuestCreateSchema()
guest_update_schema = GuestUpdateSchema()
guest_query_schema = GuestQuerySchema()
guest_create_response_schema = GuestCreateResponseSchema()
guest_list_response_schema = GuestListResponseSchema()
guest_role_option_schema = GuestRoleOptionSchema(many=True)


@api_bp.route("/members", methods=["GET"])
@jwt_required(optional=True)
def get_members_list():
    """Get a list of members with optional filtering and sorting."""
    try:
        is_leaderboard_view = request.args.get("view") == "leaderboard"
        members = MemberService.get_all_members(request.args)
        if is_leaderboard_view:
            schema = leaderboard_members_schema
        else:
            schema = members_display_schema

        return jsonify(schema.dump(members)), 200
    except Exception as e:
        current_app.logger.error(f"Error getting members list: {e}", exc_info=True)
        return jsonify(
            {"error": "server_error", "message": "獲取成員列表時發生錯誤。"}
        ), 500


@api_bp.route("/members/<int:member_id>", methods=["GET"])
@jwt_required(optional=True)
def get_single_member(member_id):
    """Get a single member by their ID."""
    member = MemberService.get_member_by_id(member_id)
    if not member:
        return jsonify({"error": "not_found", "message": "找不到指定的成員。"}), 404
    # Use the display schema for serialization
    return jsonify(member_display_schema.dump(member)), 200


@api_bp.route("/members", methods=["POST"])
@jwt_required()  # Assuming only authorized users can create members
def create_member():
    """Create a new member and associated user account."""
    json_data = request.get_json()
    if not json_data:
        return jsonify(
            {"error": "missing_json", "message": "缺少 JSON 請求內容。"}
        ), 400

    try:
        # Use the specific create schema for validation and deserialization
        validated_data = member_create_schema.load(json_data)
        new_member = MemberService.create_member_and_user(validated_data)
        return (
            jsonify(
                {
                    "message": "成員及使用者帳號已成功建立。",
                    "member": member_display_schema.dump(
                        new_member
                    ),  # Use the display schema for the response
                }
            ),
            201,
        )
    except MarshmallowValidationError as err:
        return jsonify(
            {
                "error": "validation_error",
                "message": "輸入數據有誤。",
                "details": err.messages,
            }
        ), 400
    except (UserAlreadyExistsError, AppException) as e:
        return jsonify(e.to_dict()), e.status_code
    except Exception as e:
        current_app.logger.error(f"Error creating member: {e}", exc_info=True)
        return jsonify(
            {"error": "server_error", "message": "創建成員時發生未預期錯誤。"}
        ), 500


@api_bp.route("/members/<int:member_id>", methods=["PUT"])
@jwt_required()
def update_member(member_id):
    """Update a member's profile."""
    # It's good practice to add authorization logic here.
    # For example, check if get_jwt_identity() is the member's user_id or an admin.
    member = MemberService.get_member_by_id(member_id)
    if not member:
        return jsonify({"error": "not_found", "message": "找不到要更新的成員。"}), 404

    json_data = request.get_json()
    if not json_data:
        return jsonify(
            {"error": "missing_json", "message": "缺少 JSON 請求內容。"}
        ), 400

    try:
        # Use the specific update schema for validation, allowing partial updates
        validated_data = member_update_schema.load(json_data, partial=True)
        updated_member = MemberService.update_member(member, validated_data)
        return (
            jsonify(
                {
                    "message": "成員資料已成功更新。",
                    "member": member_display_schema.dump(
                        updated_member
                    ),  # Use the display schema for the response
                }
            ),
            200,
        )
    except MarshmallowValidationError as err:
        return jsonify(
            {
                "error": "validation_error",
                "message": "輸入數據有誤。",
                "details": err.messages,
            }
        ), 400
    except (UserAlreadyExistsError, AppException) as e:
        return jsonify(e.to_dict()), e.status_code
    except Exception as e:
        current_app.logger.error(
            f"Error updating member {member_id}: {e}", exc_info=True
        )
        return jsonify(
            {"error": "server_error", "message": "更新成員資料時發生錯誤。"}
        ), 500


@api_bp.route("/members/<int:member_id>", methods=["DELETE"])
@jwt_required()
def delete_member(member_id):
    """Delete a member and their associated user account."""
    # Authorization logic is crucial here (e.g., only admins can delete)
    member = MemberService.get_member_by_id(member_id)
    if not member:
        return jsonify({"error": "not_found", "message": "找不到要刪除的成員。"}), 404

    try:
        MemberService.delete_member(member)
        return jsonify({"message": "成員已成功刪除。"}), 200
    except AppException as e:
        return jsonify(e.to_dict()), e.status_code
    except Exception as e:
        current_app.logger.error(
            f"Error deleting member {member_id}: {e}", exc_info=True
        )
        return jsonify(
            {"error": "server_error", "message": "刪除成員時發生錯誤。"}
        ), 500


@api_bp.route("/members/guests", methods=["POST"])
@jwt_required()
def create_guest():
    """在比賽中快速創建訪客球員"""
    try:
        # 驗證請求數據
        try:
            data = guest_create_schema.load(request.get_json() or {})
        except Exception as e:
            return jsonify(
                {
                    "error": "validation_error",
                    "message": "請求數據格式錯誤",
                    "details": str(e),
                }
            ), 400

        # 獲取當前用戶ID作為創建者
        current_user_id = int(get_jwt_identity())

        # 檢查姓名是否重複（同一創建者的訪客）
        existing_guest = Member.query.filter(
            Member.name == data["name"],
            Member.is_guest == True,
            Member.created_by_user_id == current_user_id,
        ).first()

        if existing_guest:
            return jsonify(
                {
                    "error": "duplicate_error",
                    "message": f"您已經創建過名為 '{data['name']}' 的訪客",
                    "existing_guest": member_display_schema.dump(existing_guest),
                }
            ), 409

        # 驗證組織是否存在（如果提供了組織ID）
        if data.get("organization_id"):
            organization = Organization.query.get(data["organization_id"])
            if not organization:
                return jsonify(
                    {"error": "validation_error", "message": "指定的組織不存在"}
                ), 400

        # 創建新訪客
        new_guest = Member.create_guest(
            name=data["name"],
            phone=data.get("phone"),
            created_by_user_id=current_user_id,
            guest_role=data.get("guest_role", GuestRoleEnum.NEUTRAL),
            organization_id=data.get("organization_id"),
            notes=data.get("notes"),
        )

        # 儲存到資料庫
        db.session.add(new_guest)
        db.session.commit()

        current_app.logger.info(
            f"用戶 {current_user_id} 創建了新訪客: {new_guest.name} (ID: {new_guest.id})"
        )

        # 返回創建的訪客資訊
        return jsonify(
            guest_create_response_schema.dump(
                {
                    "success": True,
                    "message": f"訪客 '{new_guest.name}' 創建成功",
                    "member": new_guest,
                }
            )
        ), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"創建訪客時發生錯誤: {e}", exc_info=True)
        return jsonify(
            {"error": "server_error", "message": "創建訪客時發生錯誤，請稍後重試"}
        ), 500


@api_bp.route("/members/guests/search", methods=["GET"])
@jwt_required()
def search_my_guests():
    """搜尋我創建的訪客（用於快速選擇）"""
    try:
        # 驗證查詢參數
        try:
            params = guest_query_schema.load(request.args)
        except Exception as e:
            return jsonify(
                {
                    "error": "validation_error",
                    "message": "查詢參數格式錯誤",
                    "details": str(e),
                }
            ), 400

        current_user_id = int(get_jwt_identity())

        # 構建查詢
        query = (
            Member.query.filter(
                Member.is_guest == True, Member.created_by_user_id == current_user_id
            )
            .options(joinedload(Member.organization))
            .order_by(Member.usage_count.desc(), Member.last_used_at.desc())
        )

        # 搜尋關鍵字篩選
        if params.get("q"):
            search_term = f"%{params['q']}%"
            query = query.filter(
                db.or_(
                    Member.name.ilike(search_term),
                    Member.guest_phone.ilike(search_term),
                    Member.guest_identifier.ilike(search_term),
                    Member.guest_notes.ilike(search_term),
                )
            )

        # 身份類型篩選
        if params.get("guest_role"):
            query = query.filter(Member.guest_role == params["guest_role"])

        # 組織篩選
        if params.get("organization_id"):
            query = query.filter(Member.organization_id == params["organization_id"])

        # 限制結果數量
        guests = query.limit(params.get("limit", 10)).all()

        return jsonify(
            guest_list_response_schema.dump(
                {"success": True, "guests": guests, "total": len(guests)}
            )
        ), 200

    except Exception as e:
        current_app.logger.error(f"搜尋訪客時發生錯誤: {e}", exc_info=True)
        return jsonify({"error": "server_error", "message": "搜尋訪客時發生錯誤"}), 500


@api_bp.route("/members/guests/<int:guest_id>", methods=["PUT"])
@jwt_required()
def update_guest(guest_id):
    """更新訪客資訊"""
    try:
        current_user_id = int(get_jwt_identity())

        # 查找訪客
        guest = Member.query.filter(
            Member.id == guest_id, Member.is_guest == True
        ).first()

        if not guest:
            return jsonify({"error": "not_found", "message": "訪客不存在"}), 404

        # 權限檢查：只有創建者可以修改（暫時不檢查管理員權限）
        if guest.created_by_user_id != current_user_id:
            return jsonify(
                {
                    "error": "permission_denied",
                    "message": "只有訪客創建者可以修改訪客資訊",
                }
            ), 403

        # 驗證更新數據
        try:
            data = guest_update_schema.load(request.get_json() or {})
        except Exception as e:
            return jsonify(
                {
                    "error": "validation_error",
                    "message": "更新數據格式錯誤",
                    "details": str(e),
                }
            ), 400

        # 更新訪客資訊
        guest.update_guest_info(
            name=data.get("name"),
            phone=data.get("phone"),
            guest_role=data.get("guest_role"),
            organization_id=data.get("organization_id"),
            notes=data.get("notes"),
        )

        db.session.commit()

        return jsonify(
            guest_create_response_schema.dump(
                {"success": True, "message": "訪客資訊更新成功", "member": guest}
            )
        ), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新訪客失敗: {e}", exc_info=True)
        return jsonify({"error": "server_error", "message": "更新訪客資訊失敗"}), 500


@api_bp.route("/members/guests/role-options", methods=["GET"])
@jwt_required()
def get_guest_role_options():
    """獲取訪客身份類型選項"""
    try:
        options = GuestRoleEnum.get_all_options()
        return jsonify({"success": True, "options": options}), 200

    except Exception as e:
        current_app.logger.error(f"獲取訪客身份選項失敗: {e}", exc_info=True)
        return jsonify({"error": "server_error", "message": "獲取選項失敗"}), 500


@api_bp.route("/members/guests/<int:guest_id>", methods=["DELETE"])
@jwt_required()
def delete_guest(guest_id):
    """刪除訪客"""
    try:
        current_user_id = int(get_jwt_identity())

        # 查找訪客
        guest = Member.query.filter(
            Member.id == guest_id, Member.is_guest == True
        ).first()

        if not guest:
            return jsonify({"error": "not_found", "message": "訪客不存在"}), 404

        # 權限檢查：只有創建者可以刪除
        if guest.created_by_user_id != current_user_id:
            return jsonify(
                {"error": "permission_denied", "message": "只有訪客創建者可以刪除訪客"}
            ), 403

        # 檢查是否可以安全刪除（檢查是否有比賽記錄）
        if not guest.can_be_deleted():
            return jsonify(
                {
                    "error": "constraint_error",
                    "message": "此訪客已參與比賽，無法刪除。請考慮將其設為不活躍狀態。",
                }
            ), 400

        guest_name = guest.name
        db.session.delete(guest)
        db.session.commit()

        return jsonify({"success": True, "message": f"訪客 '{guest_name}' 已刪除"}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"刪除訪客失敗: {e}", exc_info=True)
        return jsonify({"error": "server_error", "message": "刪除訪客失敗"}), 500
