# backend/app/api/match_routes.py
from flask import current_app, jsonify, request
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError as MarshmallowValidationError

from ..schemas.match_schemas import (
    MatchQuerySchema,
    MatchRecordCreateSchema,
    MatchRecordDetailedCreateSchema,
    MatchRecordDetailedResponseSchema,
    MatchRecordDetailedUpdateSchema,
    MatchRecordResponseSchema,
    MatchRecordUpdateSchema,
)
from ..services.match_service import MatchRecordService
from ..tools.exceptions import AppException
from . import api_bp

create_schema = MatchRecordCreateSchema()
detailed_create_schema = MatchRecordDetailedCreateSchema()
update_schema = MatchRecordUpdateSchema()
detailed_update_schema = MatchRecordDetailedUpdateSchema()
response_schema = MatchRecordResponseSchema()
detailed_response_schema = MatchRecordDetailedResponseSchema()
responses_schema = MatchRecordResponseSchema(many=True)
query_schema = MatchQuerySchema()


@api_bp.route("/match-records", methods=["POST"])
@jwt_required()
def create_match_record():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "missing_json", "message": "缺少 JSON 請求內容"}), 400

    try:
        validated_data = create_schema.load(json_data)
        new_record = MatchRecordService.create_match_record(validated_data)
        return jsonify({
            "message": "比賽記錄已成功建立",
            "record": response_schema.dump(new_record)
        }), 201

    except MarshmallowValidationError as err:
        return jsonify({
            "error": "validation_error",
            "message": "輸入數據有誤",
            "details": err.messages
        }), 400
    except AppException as e:
        return jsonify(e.to_dict()), e.status_code
    except Exception as e:
        current_app.logger.error(f"創建比賽記錄時發生錯誤: {e}", exc_info=True)
        return jsonify({"error": "server_error", "message": "創建時發生錯誤"}), 500


@api_bp.route("/match-records/detailed", methods=["POST"])
@jwt_required()
def create_match_record_detailed():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "missing_json", "message": "缺少 JSON 請求內容"}), 400

    try:
        validated_data = detailed_create_schema.load(json_data)
        new_record = MatchRecordService.create_match_record_detailed(validated_data)
        return jsonify({
            "message": "詳細比賽記錄已成功建立",
            "record": detailed_response_schema.dump(new_record)
        }), 201

    except MarshmallowValidationError as err:
        return jsonify({
            "error": "validation_error",
            "message": "輸入數據有誤",
            "details": err.messages
        }), 400
    except AppException as e:
        return jsonify(e.to_dict()), e.status_code
    except Exception as e:
        current_app.logger.error(f"創建詳細比賽記錄時發生錯誤: {e}", exc_info=True)
        return jsonify({"error": "server_error", "message": "創建時發生錯誤"}), 500


@api_bp.route("/match-records", methods=["GET"])
@jwt_required(optional=True)
def get_match_records():
    try:
        try:
            query_params = query_schema.load(request.args)
        except MarshmallowValidationError as err:
            return jsonify({
                "error": "validation_error",
                "message": "查詢參數有誤",
                "details": err.messages
            }), 400

        result = MatchRecordService.get_all_match_records(query_params)

        if isinstance(result, dict) and 'items' in result:
            return jsonify({
                "data": responses_schema.dump(result['items']),
                "pagination": {
                    "total": result['total'],
                    "page": result['page'],
                    "per_page": result['per_page'],
                    "pages": result['pages'],
                    "has_prev": result['has_prev'],
                    "has_next": result['has_next']
                }
            }), 200
        else:
            return jsonify({"data": responses_schema.dump(result)}), 200

    except Exception as e:
        current_app.logger.error(f"獲取比賽記錄列表時發生錯誤: {e}", exc_info=True)
        return jsonify({"error": "server_error", "message": "獲取數據時發生錯誤"}), 500


@api_bp.route("/match-records/<int:record_id>", methods=["GET"])
@jwt_required(optional=True)
def get_match_record(record_id):
    try:
        record = MatchRecordService.get_match_record_by_id(record_id)
        if not record:
            return jsonify({"error": "not_found", "message": "找不到指定的比賽記錄"}), 404

        return jsonify({"record": response_schema.dump(record)}), 200

    except Exception as e:
        current_app.logger.error(f"獲取比賽記錄時發生錯誤: {e}", exc_info=True)
        return jsonify({"error": "server_error", "message": "獲取數據時發生錯誤"}), 500


@api_bp.route("/match-records/<int:record_id>/detailed", methods=["GET"])
@jwt_required(optional=True)
def get_match_record_detailed(record_id):
    try:
        record = MatchRecordService.get_match_record_by_id(record_id)
        if not record:
            return jsonify({"error": "not_found", "message": "找不到指定的比賽記錄"}), 404

        return jsonify({"record": detailed_response_schema.dump(record)}), 200

    except Exception as e:
        current_app.logger.error(f"獲取詳細比賽記錄時發生錯誤: {e}", exc_info=True)
        return jsonify({"error": "server_error", "message": "獲取數據時發生錯誤"}), 500


@api_bp.route("/match-records/<int:record_id>", methods=["PUT"])
@jwt_required()
def update_match_record(record_id):
    record = MatchRecordService.get_match_record_by_id(record_id)
    if not record:
        return jsonify({"error": "not_found", "message": "找不到要更新的比賽記錄"}), 404

    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "missing_json", "message": "缺少 JSON 請求內容"}), 400

    try:
        validated_data = update_schema.load(json_data, partial=True)
        updated_record = MatchRecordService.update_match_record(record_id, validated_data)

        return jsonify({
            "message": "比賽記錄已成功更新",
            "record": response_schema.dump(updated_record)
        }), 200

    except MarshmallowValidationError as err:
        return jsonify({
            "error": "validation_error",
            "message": "輸入數據有誤",
            "details": err.messages
        }), 400
    except AppException as e:
        return jsonify(e.to_dict()), e.status_code
    except Exception as e:
        current_app.logger.error(f"更新比賽記錄時發生錯誤: {e}", exc_info=True)
        return jsonify({"error": "server_error", "message": "更新時發生錯誤"}), 500


@api_bp.route("/match-records/<int:record_id>/detailed", methods=["PUT"])
@jwt_required()
def update_match_record_detailed(record_id):
    record = MatchRecordService.get_match_record_by_id(record_id)
    if not record:
        return jsonify({"error": "not_found", "message": "找不到要更新的比賽記錄"}), 404

    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "missing_json", "message": "缺少 JSON 請求內容"}), 400

    try:
        validated_data = detailed_update_schema.load(json_data, partial=True)
        updated_record = MatchRecordService.update_match_record_detailed(record_id, validated_data)

        return jsonify({
            "message": "詳細比賽記錄已成功更新",
            "record": detailed_response_schema.dump(updated_record)
        }), 200

    except MarshmallowValidationError as err:
        return jsonify({
            "error": "validation_error",
            "message": "輸入數據有誤",
            "details": err.messages
        }), 400
    except AppException as e:
        return jsonify(e.to_dict()), e.status_code
    except Exception as e:
        current_app.logger.error(f"更新詳細比賽記錄時發生錯誤: {e}", exc_info=True)
        return jsonify({"error": "server_error", "message": "更新時發生錯誤"}), 500


@api_bp.route("/match-records/<int:record_id>", methods=["DELETE"])
@jwt_required()
def delete_match_record(record_id):
    record = MatchRecordService.get_match_record_by_id(record_id)
    if not record:
        return jsonify({"error": "not_found", "message": "找不到要刪除的比賽記錄"}), 404

    try:
        MatchRecordService.delete_match_record(record)
        return jsonify({"message": "比賽記錄已成功刪除"}), 200
    except AppException as e:
        return jsonify(e.to_dict()), e.status_code
    except Exception as e:
        current_app.logger.error(f"刪除比賽記錄時發生錯誤: {e}", exc_info=True)
        return jsonify({"error": "server_error", "message": "刪除時發生錯誤"}), 500
