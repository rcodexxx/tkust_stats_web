# backend/app/api/match_routes.py
from flask import current_app, jsonify, request
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError as MarshmallowValidationError

from ..schemas.match_schemas import (
    MatchBasicSchema,
    MatchQuerySchema,
    MatchRecordCreateSchema,
    MatchRecordResponseSchema,
    MatchUpdateSchema,
)
from ..services.match_service import MatchRecordService
from ..tools.exceptions import AppException, ValidationError
from . import api_bp

# 實例化 Schemas
create_schema = MatchRecordCreateSchema()
response_schema = MatchRecordResponseSchema()
responses_schema = MatchRecordResponseSchema(many=True)
update_schema = MatchUpdateSchema()
query_schema = MatchQuerySchema()
basic_schema = MatchBasicSchema()


@api_bp.route("/match-records", methods=["POST"])
@jwt_required()
def create_match_record():
    """
    創建一場新的比賽記錄。
    包含所有新增的場地、時間、時長等資訊。
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
    """
    獲取比賽記錄列表，支援篩選、排序和分頁。
    支援的查詢參數：
    - start_date, end_date: 日期範圍
    - match_type, match_format: 比賽類型和賽制
    - court_surface, court_environment, time_slot: 場地相關
    - player_id: 球員篩選
    - page, per_page: 分頁
    - sort_by, sort_order: 排序
    """
    try:
        # 驗證查詢參數
        try:
            query_params = query_schema.load(request.args)
        except MarshmallowValidationError as err:
            return jsonify({"error": "validation_error", "message": "查詢參數有誤。", "details": err.messages}), 400

        # 獲取記錄（可能包含分頁資訊）
        result = MatchRecordService.get_all_match_records(query_params)

        # 檢查是否有分頁資訊
        if isinstance(result, dict) and 'items' in result:
            # 有分頁的回應
            return jsonify({
                "match_records": responses_schema.dump(result['items']),
                "pagination": {
                    "total": result['total'],
                    "page": result['page'],
                    "per_page": result['per_page'],
                    "pages": result['pages'],
                    "has_next": result['has_next'],
                    "has_prev": result['has_prev'],
                }
            }), 200
        else:
            # 沒有分頁的回應（向後相容）
            return jsonify({"match_records": responses_schema.dump(result)}), 200

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
        return jsonify({"match_record": response_schema.dump(record)}), 200
    except Exception as e:
        current_app.logger.error(f"獲取比賽記錄 ID {record_id} 時發生錯誤: {e}", exc_info=True)
        return jsonify({"error": "server_error", "message": "獲取記錄時發生錯誤。"}), 500


@api_bp.route("/match-records/<int:record_id>", methods=["PUT"])
@jwt_required()
def update_match_record(record_id):
    """
    更新比賽記錄。
    可以更新比賽的基本資訊、場地資訊、比分等。
    """
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "missing_json", "message": "缺少 JSON 請求內容。"}), 400

    try:
        # 驗證更新數據
        validated_data = update_schema.load(json_data)

        # 執行更新
        updated_record = MatchRecordService.update_match_record(record_id, validated_data)

        return jsonify({
            "message": "比賽記錄已成功更新。",
            "match_record": response_schema.dump(updated_record)
        }), 200

    except MarshmallowValidationError as err:
        return jsonify({"error": "validation_error", "message": "輸入數據有誤。", "details": err.messages}), 400
    except AppException as e:
        return jsonify(e.to_dict() if hasattr(e, "to_dict") else {"error": str(e)}), getattr(e, "status_code", 400)
    except Exception as e:
        current_app.logger.error(f"更新比賽記錄 ID {record_id} 時發生錯誤: {e}", exc_info=True)
        return jsonify({"error": "server_error", "message": "更新比賽記錄時發生錯誤。"}), 500


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
        return jsonify(e.to_dict() if hasattr(e, "to_dict") else {"error": str(e)}), getattr(e, "status_code", 400)
    except Exception as e:
        current_app.logger.error(f"刪除比賽記錄 ID {record_id} 時發生錯誤: {e}", exc_info=True)
        return jsonify({"error": "server_error", "message": "刪除比賽記錄時發生錯誤。"}), 500


@api_bp.route("/match-records/statistics", methods=["GET"])
def get_match_statistics():
    """
    獲取比賽統計資訊。
    支援與列表相同的篩選參數來計算特定條件下的統計。
    """
    try:
        # 驗證查詢參數（重用查詢 schema）
        try:
            query_params = query_schema.load(request.args)
        except MarshmallowValidationError as err:
            return jsonify({"error": "validation_error", "message": "查詢參數有誤。", "details": err.messages}), 400

        # 獲取統計資訊
        statistics = MatchRecordService.get_match_statistics(query_params)

        return jsonify({
            "statistics": statistics,
            "filters_applied": query_params
        }), 200

    except Exception as e:
        current_app.logger.error(f"獲取比賽統計時發生錯誤: {e}", exc_info=True)
        return jsonify({"error": "server_error", "message": "獲取統計資訊時發生錯誤。"}), 500


# --- 附加的實用 API 端點 ---

@api_bp.route("/match-records/recent", methods=["GET"])
def get_recent_matches():
    """獲取最近的比賽記錄（簡化版本）"""
    try:
        limit = min(int(request.args.get('limit', 10)), 50)  # 限制最多50筆

        result = MatchRecordService.get_all_match_records({
            'per_page': limit,
            'page': 1,
            'sort_by': 'match_date',
            'sort_order': 'desc'
        })

        # 使用基本 schema 減少資料量
        if isinstance(result, dict) and 'items' in result:
            matches = [record.match for record in result['items'] if record.match]
            return jsonify({
                "recent_matches": [basic_schema.dump(match) for match in matches]
            }), 200
        else:
            matches = [record.match for record in result if record.match]
            return jsonify({
                "recent_matches": [basic_schema.dump(match) for match in matches]
            }), 200

    except Exception as e:
        current_app.logger.error(f"獲取最近比賽時發生錯誤: {e}", exc_info=True)
        return jsonify({"error": "server_error", "message": "獲取最近比賽時發生錯誤。"}), 500


@api_bp.route("/match-records/player/<int:player_id>", methods=["GET"])
def get_player_match_history(player_id):
    """獲取特定球員的比賽歷史"""
    try:
        # 驗證查詢參數
        try:
            query_params = query_schema.load(request.args)
        except MarshmallowValidationError as err:
            return jsonify({"error": "validation_error", "message": "查詢參數有誤。", "details": err.messages}), 400

        # 強制設定 player_id
        query_params['player_id'] = player_id

        result = MatchRecordService.get_all_match_records(query_params)

        if isinstance(result, dict) and 'items' in result:
            return jsonify({
                "match_records": responses_schema.dump(result['items']),
                "pagination": {
                    "total": result['total'],
                    "page": result['page'],
                    "per_page": result['per_page'],
                    "pages": result['pages'],
                    "has_next": result['has_next'],
                    "has_prev": result['has_prev'],
                },
                "player_id": player_id
            }), 200
        else:
            return jsonify({
                "match_records": responses_schema.dump(result),
                "player_id": player_id
            }), 200

    except Exception as e:
        current_app.logger.error(f"獲取球員 {player_id} 比賽歷史時發生錯誤: {e}", exc_info=True)
        return jsonify({"error": "server_error", "message": "獲取球員比賽歷史時發生錯誤。"}), 500
