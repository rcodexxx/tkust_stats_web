# backend/app/api/organization_routes.py
from flask import jsonify, request, current_app
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError as MarshmallowValidationError

from . import api_bp  # 您的 API 藍圖
from ..schemas.organization_schemas import OrganizationSchema, OrganizationCreateSchema, OrganizationUpdateSchema
from ..services.organization_service import (
    OrganizationService,
    OrganizationNotFoundError,
    OrganizationInUseError,
    OrganizationAlreadyExistsError,
)
from ..tools.exceptions import AppException

# 實例化 Schemas 以便在路由中使用
org_schema = OrganizationSchema()
orgs_schema = OrganizationSchema(many=True)
org_create_schema = OrganizationCreateSchema()
org_update_schema = OrganizationUpdateSchema()


@api_bp.route("/organizations", methods=["GET"])
def get_organizations():
    """獲取所有組織的列表。"""
    try:
        orgs = OrganizationService.get_all_organizations(request.args)
        # 在序列化前，將成員數量附加到每個組織物件上
        for org in orgs:
            org.members_count = len(org.members)
        return jsonify(orgs_schema.dump(orgs)), 200
    except Exception as e:
        current_app.logger.error(f"獲取組織列表時發生錯誤: {e}", exc_info=True)
        return jsonify({"error": "server_error", "message": "獲取組織列表時發生伺服器錯誤。"}), 500


@api_bp.route("/organizations/<int:org_id>", methods=["GET"])
def get_organization(org_id):
    """根據 ID 獲取單一組織的詳細資訊。"""
    try:
        org = OrganizationService.get_organization_by_id(org_id)
        if not org:
            raise OrganizationNotFoundError()  # 拋出業務異常

        org.members_count = len(org.members)
        return jsonify(org_schema.dump(org)), 200
    except OrganizationNotFoundError as e:
        return jsonify(e.to_dict()), e.status_code
    except Exception as e:
        current_app.logger.error(f"獲取組織 ID {org_id} 時發生錯誤: {e}", exc_info=True)
        return jsonify({"error": "server_error", "message": "獲取組織資訊時發生伺服器錯誤。"}), 500


@api_bp.route("/organizations", methods=["POST"])
@jwt_required()  # 假設只有認證後的使用者 (例如管理員) 可以創建組織
def create_organization():
    """創建一個新的組織。"""
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "missing_json", "message": "缺少 JSON 請求內容。"}), 400

    try:
        validated_data = org_create_schema.load(json_data)
        new_org = OrganizationService.create_organization(validated_data)
        return jsonify({"message": "組織已成功建立。", "organization": org_schema.dump(new_org)}), 201
    except MarshmallowValidationError as err:
        return jsonify({"error": "validation_error", "message": "輸入數據有誤。", "details": err.messages}), 400
    except (OrganizationAlreadyExistsError, AppException) as e:
        return jsonify(e.to_dict()), e.status_code
    except Exception as e:
        current_app.logger.error(f"創建組織時發生錯誤: {e}", exc_info=True)
        return jsonify({"error": "server_error", "message": "創建組織時發生未預期錯誤。"}), 500


@api_bp.route("/organizations/<int:org_id>", methods=["PUT"])
@jwt_required()  # 假設只有認證後的使用者可以更新
def update_organization(org_id):
    """更新一個已存在的組織。"""
    org = OrganizationService.get_organization_by_id(org_id)
    if not org:
        return jsonify({"error": "not_found", "message": "找不到要更新的組織。"}), 404

    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "missing_json", "message": "缺少 JSON 請求內容。"}), 400

    try:
        # partial=True 允許部分更新
        validated_data = org_update_schema.load(json_data, partial=True)
        updated_org = OrganizationService.update_organization(org, validated_data)
        return jsonify({"message": "組織資料已成功更新。", "organization": org_schema.dump(updated_org)}), 200
    except MarshmallowValidationError as err:
        return jsonify({"error": "validation_error", "message": "輸入數據有誤。", "details": err.messages}), 400
    except (OrganizationAlreadyExistsError, AppException) as e:
        return jsonify(e.to_dict()), e.status_code
    except Exception as e:
        current_app.logger.error(f"更新組織 ID {org_id} 時發生錯誤: {e}", exc_info=True)
        return jsonify({"error": "server_error", "message": "更新組織資料時發生錯誤。"}), 500


@api_bp.route("/organizations/<int:org_id>", methods=["DELETE"])
@jwt_required()  # 假設只有認證後的使用者可以刪除
def delete_organization(org_id):
    """刪除一個組織。"""
    org = OrganizationService.get_organization_by_id(org_id)
    if not org:
        return jsonify({"error": "not_found", "message": "找不到要刪除的組織。"}), 404

    try:
        OrganizationService.delete_organization(org)
        return jsonify({"message": "組織已成功刪除。"}), 200
    except (OrganizationInUseError, AppException) as e:
        return jsonify(e.to_dict()), e.status_code
    except Exception as e:
        current_app.logger.error(f"刪除組織 ID {org_id} 時發生錯誤: {e}", exc_info=True)
        return jsonify({"error": "server_error", "message": "刪除組織時發生錯誤。"}), 500
