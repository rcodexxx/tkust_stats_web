# your_project/app/api/match_record_routes.py
from flask import jsonify, request, current_app
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError as MarshmallowValidationError

from . import api_bp
from ..schemas.match_schemas import MatchRecordCreateSchema, MatchRecordResponseSchema
from ..services.match_service import MatchRecordService
from ..tools.exceptions import AppException, ValidationError

# 實例化 Schemas
create_schema = MatchRecordCreateSchema()
response_schema = MatchRecordResponseSchema()
responses_schema = MatchRecordResponseSchema(many=True)


@api_bp.route("/match-records", methods=["POST"])
@jwt_required()
def create_match_record():
    """
    創建一場新的比賽記錄。
    此路由取代了舊的 /matches/record。
    """
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "missing_json", "message": "缺少 JSON 請求內容。"}), 400

    try:
        # 1. 使用 Schema 驗證請求數據
        validated_data = create_schema.load(json_data)

        # 2. 調用服務層來執行創建邏輯
        new_record = MatchRecordService.create_match_record(validated_data)

        # 3. 序列化並返回成功回應
        return (
            jsonify(
                {
                    "message": "比賽記錄已成功創建，相關球員評分已更新。",
                    "match_record": response_schema.dump(new_record),
                }
            ),
            201,
        )

    except MarshmallowValidationError as err:
        # 處理 Schema 驗證失敗的錯誤
        return jsonify({"error": "validation_error", "message": "輸入數據有誤。", "details": err.messages}), 400
    except (ValidationError, AppException) as e:
        # 處理服務層拋出的自訂業務異常
        return jsonify(e.to_dict() if hasattr(e, "to_dict") else {"error": str(e)}), getattr(e, "status_code", 400)
    except Exception as e:
        # 處理未預期的伺服器錯誤
        current_app.logger.error(f"創建比賽記錄時發生錯誤: {e}", exc_info=True)
        return jsonify({"error": "server_error", "message": "創建比賽記錄時發生未預期錯誤。"}), 500


@api_bp.route("/match-records", methods=["GET"])
def get_all_match_records():
    """獲取比賽記錄列表。"""
    try:
        records = MatchRecordService.get_all_match_records(request.args)
        return jsonify(responses_schema.dump(records)), 200
    except Exception as e:
        current_app.logger.error(f"獲取比賽記錄列表時發生錯誤: {e}", exc_info=True)
        return jsonify({"error": "server_error", "message": "獲取列表時發生錯誤。"}), 500


@api_bp.route("/match-records/<int:record_id>", methods=["GET"])
def get_single_match_record(record_id):
    """根據 ID 獲取單場比賽記錄的詳細資訊。"""
    try:
        record = MatchRecordService.get_match_record_by_id(record_id)
        if not record:
            return jsonify({"error": "not_found", "message": "找不到指定的比賽記錄。"}), 404
        return jsonify(response_schema.dump(record)), 200
    except Exception as e:
        current_app.logger.error(f"獲取比賽記錄 ID {record_id} 時發生錯誤: {e}", exc_info=True)
        return jsonify({"error": "server_error", "message": "獲取記錄時發生錯誤。"}), 500


@api_bp.route("/match-records/<int:record_id>", methods=["DELETE"])
@jwt_required()
def delete_match_record(record_id):
    """刪除一場比賽記錄，並觸發相關球員評分的重新計算。"""

    record = MatchRecordService.get_match_record_by_id(record_id)
    if not record:
        return jsonify({"error": "not_found", "message": "找不到要刪除的比賽記錄。"}), 404

    try:
        MatchRecordService.delete_match_record(record)
        return jsonify({"message": "比賽記錄已成功刪除，相關球員評分已更新。"}), 200
    except AppException as e:
        return jsonify(e.to_dict()), e.status_code
    except Exception as e:
        current_app.logger.error(f"刪除比賽記錄 ID {record_id} 時發生錯誤: {e}", exc_info=True)
        return jsonify({"error": "server_error", "message": "刪除比賽記錄時發生錯誤。"}), 500
