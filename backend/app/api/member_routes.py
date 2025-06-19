# backend/app/api/member_routes.py
"""
Member API Routes - 球員管理與四維度評分系統

主要功能模塊：
1. 基本 CRUD 操作
2. 訪客管理系統
3. 排行榜與評分系統
4. 統計與比較功能
"""

from flask import current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from marshmallow import ValidationError
from sqlalchemy.orm import joinedload

from ..extensions import db
from ..models import Member, Organization
from ..models.enums import GuestRoleEnum
from ..schemas.member_schemas import (
    GuestCreateResponseSchema,
    GuestCreateSchema,
    GuestListResponseSchema,
    GuestQuerySchema,
    GuestUpdateSchema,
    MemberCreateSchema,
    MemberSchema,
    MemberUpdateSchema,
)
from ..services.member_service import MemberService
from ..tools.exceptions import AppException, UserAlreadyExistsError
from . import api_bp

# ===== Schema 實例化 =====
# 基本 Member Schemas
member_schema = MemberSchema()
members_schema = MemberSchema(many=True)
member_create_schema = MemberCreateSchema()
member_update_schema = MemberUpdateSchema()

# 訪客 Schemas
guest_create_schema = GuestCreateSchema()
guest_update_schema = GuestUpdateSchema()
guest_query_schema = GuestQuerySchema()
guest_response_schema = GuestCreateResponseSchema()
guest_list_schema = GuestListResponseSchema()


# ===== 輔助函數 =====
def handle_validation_error(error: ValidationError, message: str = "輸入數據有誤"):
    """統一處理驗證錯誤"""
    return jsonify(
        {
            "error": "validation_error",
            "message": message,
            "details": error.messages,
        }
    ), 400


def handle_app_exception(error: AppException):
    """統一處理應用程式異常"""
    return jsonify(error.to_dict()), error.status_code


def handle_server_error(error: Exception, message: str, operation: str = ""):
    """統一處理伺服器錯誤"""
    current_app.logger.error(f"Error in {operation}: {error}", exc_info=True)
    return jsonify({"error": "server_error", "message": message}), 500


def get_current_user_id() -> int:
    """獲取當前用戶 ID"""
    return int(get_jwt_identity())


# ===== 基本 CRUD 操作 =====
@api_bp.route("/members", methods=["GET"])
@jwt_required(optional=True)
def get_members_list():
    """
    獲取球員列表

    查詢參數：
    - view: 'leaderboard' 使用排行榜視圖
    - 其他篩選參數由 MemberService 處理
    """
    try:
        # 判斷是否為排行榜視圖（向後兼容）
        if request.args.get("view") == "leaderboard":
            return _get_leaderboard_legacy()

        # 一般會員列表
        members = MemberService.get_all_members(request.args)
        return jsonify(members_schema.dump(members)), 200

    except Exception as e:
        return handle_server_error(e, "獲取成員列表時發生錯誤", "get_members_list")


def _get_leaderboard_legacy():
    """向後兼容的排行榜視圖"""
    from .leaderboard_routes import get_leaderboard

    return get_leaderboard()


@api_bp.route("/members/<int:member_id>", methods=["GET"])
@jwt_required(optional=True)
def get_single_member(member_id):
    """獲取單一球員詳細資訊"""
    member = MemberService.get_member_by_id(member_id)
    if not member:
        return jsonify({"error": "not_found", "message": "找不到指定的成員"}), 404

    return jsonify(member_schema.dump(member)), 200


@api_bp.route("/members", methods=["POST"])
@jwt_required()
def create_member():
    """創建新的正式會員"""
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "missing_json", "message": "缺少 JSON 請求內容"}), 400

    try:
        validated_data = member_create_schema.load(json_data)
        new_member = MemberService.create_member_and_user(validated_data)

        return jsonify(
            {
                "message": "成員及使用者帳號已成功建立",
                "member": member_schema.dump(new_member),
            }
        ), 201

    except ValidationError as err:
        return handle_validation_error(err)
    except (UserAlreadyExistsError, AppException) as e:
        return handle_app_exception(e)
    except Exception as e:
        return handle_server_error(e, "創建成員時發生未預期錯誤", "create_member")


@api_bp.route("/members/<int:member_id>", methods=["PUT"])
@jwt_required()
def update_member(member_id):
    """更新球員資料"""
    member = MemberService.get_member_by_id(member_id)
    if not member:
        return jsonify({"error": "not_found", "message": "找不到要更新的成員"}), 404

    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "missing_json", "message": "缺少 JSON 請求內容"}), 400

    try:
        validated_data = member_update_schema.load(json_data, partial=True)
        updated_member = MemberService.update_member(member, validated_data)

        return jsonify(
            {
                "message": "成員資料已成功更新",
                "member": member_schema.dump(updated_member),
            }
        ), 200

    except ValidationError as err:
        return handle_validation_error(err)
    except (UserAlreadyExistsError, AppException) as e:
        return handle_app_exception(e)
    except Exception as e:
        return handle_server_error(e, "更新成員資料時發生錯誤", "update_member")


@api_bp.route("/members/<int:member_id>", methods=["DELETE"])
@jwt_required()
def delete_member(member_id):
    """刪除球員及相關帳號"""
    member = MemberService.get_member_by_id(member_id)
    if not member:
        return jsonify({"error": "not_found", "message": "找不到要刪除的成員"}), 404

    try:
        MemberService.delete_member(member)
        return jsonify({"message": "成員已成功刪除"}), 200

    except AppException as e:
        return handle_app_exception(e)
    except Exception as e:
        return handle_server_error(e, "刪除成員時發生錯誤", "delete_member")


# ===== 訪客管理系統 =====
@api_bp.route("/members/guests", methods=["POST"])
@jwt_required()
def create_guest():
    """創建新訪客球員"""
    try:
        data = guest_create_schema.load(request.get_json() or {})
        current_user_id = get_current_user_id()

        # 檢查重複名稱
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
                    "existing_guest": member_schema.dump(existing_guest),
                }
            ), 409

        # 驗證組織
        if data.get("organization_id"):
            organization = Organization.query.get(data["organization_id"])
            if not organization:
                return jsonify(
                    {"error": "validation_error", "message": "指定的組織不存在"}
                ), 400

        # 創建訪客
        new_guest = Member.create_guest(
            name=data["name"],
            phone=data.get("phone"),
            created_by_user_id=current_user_id,
            guest_role=data.get("guest_role", GuestRoleEnum.NEUTRAL),
            organization_id=data.get("organization_id"),
            notes=data.get("notes"),
        )

        db.session.add(new_guest)
        db.session.commit()

        current_app.logger.info(
            f"用戶 {current_user_id} 創建了新訪客: {new_guest.name} (ID: {new_guest.id})"
        )

        return jsonify(
            guest_response_schema.dump(
                {
                    "success": True,
                    "message": f"訪客 '{new_guest.name}' 創建成功",
                    "member": new_guest,
                }
            )
        ), 201

    except ValidationError as err:
        return handle_validation_error(err, "請求數據格式錯誤")
    except Exception as e:
        db.session.rollback()
        return handle_server_error(e, "創建訪客時發生錯誤", "create_guest")


@api_bp.route("/members/guests/search", methods=["GET"])
@jwt_required()
def search_my_guests():
    """搜尋我創建的訪客"""
    try:
        params = guest_query_schema.load(request.args)
        current_user_id = get_current_user_id()

        # 構建查詢
        query = (
            Member.query.filter(
                Member.is_guest == True, Member.created_by_user_id == current_user_id
            )
            .options(joinedload(Member.organization))
            .order_by(Member.usage_count.desc(), Member.last_used_at.desc())
        )

        # 應用篩選
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

        if params.get("guest_role"):
            query = query.filter(Member.guest_role == params["guest_role"])

        if params.get("organization_id"):
            query = query.filter(Member.organization_id == params["organization_id"])

        guests = query.limit(params.get("limit", 10)).all()

        return jsonify(
            guest_list_schema.dump(
                {"success": True, "guests": guests, "total": len(guests)}
            )
        ), 200

    except ValidationError as err:
        return handle_validation_error(err, "查詢參數格式錯誤")
    except Exception as e:
        return handle_server_error(e, "搜尋訪客時發生錯誤", "search_my_guests")


@api_bp.route("/members/guests/<int:guest_id>", methods=["PUT"])
@jwt_required()
def update_guest(guest_id):
    """更新訪客資訊"""
    try:
        current_user_id = get_current_user_id()

        guest = Member.query.filter(
            Member.id == guest_id, Member.is_guest == True
        ).first()

        if not guest:
            return jsonify({"error": "not_found", "message": "訪客不存在"}), 404

        # 權限檢查
        if guest.created_by_user_id != current_user_id:
            return jsonify(
                {
                    "error": "permission_denied",
                    "message": "只有訪客創建者可以修改訪客資訊",
                }
            ), 403

        data = guest_update_schema.load(request.get_json() or {})

        guest.update_guest_info(
            name=data.get("name"),
            phone=data.get("phone"),
            guest_role=data.get("guest_role"),
            organization_id=data.get("organization_id"),
            notes=data.get("notes"),
        )

        db.session.commit()

        return jsonify(
            guest_response_schema.dump(
                {"success": True, "message": "訪客資訊更新成功", "member": guest}
            )
        ), 200

    except ValidationError as err:
        return handle_validation_error(err, "更新數據格式錯誤")
    except Exception as e:
        db.session.rollback()
        return handle_server_error(e, "更新訪客資訊失敗", "update_guest")


@api_bp.route("/members/guests/<int:guest_id>", methods=["DELETE"])
@jwt_required()
def delete_guest(guest_id):
    """刪除訪客"""
    try:
        current_user_id = get_current_user_id()

        guest = Member.query.filter(
            Member.id == guest_id, Member.is_guest == True
        ).first()

        if not guest:
            return jsonify({"error": "not_found", "message": "訪客不存在"}), 404

        # 權限檢查
        if guest.created_by_user_id != current_user_id:
            return jsonify(
                {"error": "permission_denied", "message": "只有訪客創建者可以刪除訪客"}
            ), 403

        # 安全檢查
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
        return handle_server_error(e, "刪除訪客失敗", "delete_guest")


@api_bp.route("/members/guests/role-options", methods=["GET"])
@jwt_required()
def get_guest_role_options():
    """獲取訪客身份類型選項"""
    try:
        options = GuestRoleEnum.get_all_options()
        return jsonify({"success": True, "options": options}), 200

    except Exception as e:
        return handle_server_error(e, "獲取選項失敗", "get_guest_role_options")
