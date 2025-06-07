# your_project/app/api/member_routes.py
from flask import jsonify, request, current_app
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError as MarshmallowValidationError

from . import api_bp  # Assuming your Blueprint is named api_bp
from ..schemas.member_schemas import MemberSchema, MemberCreateSchema, MemberUpdateSchema
from ..services.member_service import MemberService
from ..tools.exceptions import AppException, UserAlreadyExistsError

# Instantiate all necessary schemas
member_display_schema = MemberSchema()
members_display_schema = MemberSchema(many=True)
member_create_schema = MemberCreateSchema()
member_update_schema = MemberUpdateSchema()


@api_bp.route("/members", methods=["GET"])
@jwt_required(optional=True)
def get_members_list():
    """Get a list of members with optional filtering and sorting."""
    try:
        members = MemberService.get_all_members(request.args)
        # Use the display schema for serialization
        return jsonify(members_display_schema.dump(members)), 200
    except Exception as e:
        current_app.logger.error(f"Error getting members list: {e}", exc_info=True)
        return jsonify({"error": "server_error", "message": "獲取成員列表時發生錯誤。"}), 500


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
        return jsonify({"error": "missing_json", "message": "缺少 JSON 請求內容。"}), 400

    try:
        # Use the specific create schema for validation and deserialization
        validated_data = member_create_schema.load(json_data)
        new_member = MemberService.create_member_and_user(validated_data)
        return jsonify({
            "message": "成員及使用者帳號已成功建立。",
            "member": member_display_schema.dump(new_member)  # Use the display schema for the response
        }), 201
    except MarshmallowValidationError as err:
        return jsonify({"error": "validation_error", "message": "輸入數據有誤。", "details": err.messages}), 400
    except (UserAlreadyExistsError, AppException) as e:
        return jsonify(e.to_dict()), e.status_code
    except Exception as e:
        current_app.logger.error(f"Error creating member: {e}", exc_info=True)
        return jsonify({"error": "server_error", "message": "創建成員時發生未預期錯誤。"}), 500


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
        return jsonify({"error": "missing_json", "message": "缺少 JSON 請求內容。"}), 400

    try:
        # Use the specific update schema for validation, allowing partial updates
        validated_data = member_update_schema.load(json_data, partial=True)
        updated_member = MemberService.update_member(member, validated_data)
        return jsonify({
            "message": "成員資料已成功更新。",
            "member": member_display_schema.dump(updated_member) # Use the display schema for the response
        }), 200
    except MarshmallowValidationError as err:
        return jsonify({"error": "validation_error", "message": "輸入數據有誤。", "details": err.messages}), 400
    except (UserAlreadyExistsError, AppException) as e:
        return jsonify(e.to_dict()), e.status_code
    except Exception as e:
        current_app.logger.error(f"Error updating member {member_id}: {e}", exc_info=True)
        return jsonify({"error": "server_error", "message": "更新成員資料時發生錯誤。"}), 500


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
        current_app.logger.error(f"Error deleting member {member_id}: {e}", exc_info=True)
        return jsonify({"error": "server_error", "message": "刪除成員時發生錯誤。"}), 500
