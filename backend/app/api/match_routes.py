# backend/app/api/match_routes.py (修改版本)
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
    🔧 修改：加入詳細的分數驗證錯誤回饋
    """
    json_data = request.get_json()
    if not json_data:
        return jsonify(
            {"error": "missing_json", "message": "缺少 JSON 請求內容。"}
        ), 400

    try:
        # 1. 使用 Schema 驗證請求數據
        validated_data = create_schema.load(json_data)

        # 🔧 新增：在服務層執行前，先進行分數預驗證
        if all(key in validated_data for key in ["a_games", "b_games", "match_format"]):
            is_valid, error_msg = MatchRecordService._validate_match_score(
                validated_data["a_games"],
                validated_data["b_games"],
                validated_data["match_format"],
            )

            if not is_valid:
                return jsonify(
                    {
                        "error": "score_validation_error",
                        "message": "比賽分數不符合規則",
                        "details": {"score_validation": [error_msg]},
                        "score_info": {
                            "a_games": validated_data["a_games"],
                            "b_games": validated_data["b_games"],
                            "match_format": validated_data["match_format"],
                            "games_to_win": MatchRecordService._get_games_to_win(
                                validated_data["match_format"]
                            ),
                        },
                    }
                ), 400

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
        return jsonify(
            {
                "error": "validation_error",
                "message": "輸入數據有誤。",
                "details": err.messages,
            }
        ), 400
    except ValidationError as e:
        # 🔧 修改：處理分數驗證錯誤，提供更詳細的錯誤信息
        return jsonify(
            {
                "error": "score_validation_error",
                "message": str(e),
                "details": {"score_validation": [str(e)]},
                "score_info": {
                    "a_games": json_data.get("a_games"),
                    "b_games": json_data.get("b_games"),
                    "match_format": json_data.get("match_format"),
                    "games_to_win": MatchRecordService._get_games_to_win(
                        json_data.get("match_format", "games_9")
                    ),
                },
            }
        ), 400
    except AppException as e:
        return jsonify(
            e.to_dict() if hasattr(e, "to_dict") else {"error": str(e)}
        ), getattr(e, "status_code", 400)
    except Exception as e:
        # 處理未預期的伺服器錯誤
        current_app.logger.error(f"創建比賽記錄時發生錯誤: {e}", exc_info=True)
        return jsonify(
            {"error": "server_error", "message": "創建比賽記錄時發生未預期錯誤。"}
        ), 500


@api_bp.route("/match-records/<int:record_id>", methods=["PUT"])
@jwt_required()
def update_match_record(record_id):
    """
    更新比賽記錄。
    🔧 修改：加入詳細的分數驗證錯誤回饋
    """
    json_data = request.get_json()
    if not json_data:
        return jsonify(
            {"error": "missing_json", "message": "缺少 JSON 請求內容。"}
        ), 400

    try:
        # 驗證更新數據
        validated_data = update_schema.load(json_data)

        # 🔧 新增：如果更新包含分數，先進行預驗證
        if any(key in validated_data for key in ["a_games", "b_games", "match_format"]):
            # 獲取當前記錄以填補缺失的值
            current_record = MatchRecordService.get_match_record_by_id(record_id)
            if not current_record:
                return jsonify(
                    {"error": "not_found", "message": "找不到要更新的比賽記錄。"}
                ), 404

            # 組合新舊值進行驗證
            new_a_games = validated_data.get("a_games", current_record.a_games)
            new_b_games = validated_data.get("b_games", current_record.b_games)
            new_format = validated_data.get(
                "match_format",
                current_record.match.match_format.value
                if current_record.match.match_format
                else "games_9",
            )

            # 預驗證分數
            is_valid, error_msg = MatchRecordService._validate_match_score(
                new_a_games, new_b_games, new_format
            )

            if not is_valid:
                return jsonify(
                    {
                        "error": "score_validation_error",
                        "message": "比賽分數不符合規則",
                        "details": {"score_validation": [error_msg]},
                        "score_info": {
                            "a_games": new_a_games,
                            "b_games": new_b_games,
                            "match_format": new_format,
                            "games_to_win": MatchRecordService._get_games_to_win(
                                new_format
                            ),
                            "current_values": {
                                "a_games": current_record.a_games,
                                "b_games": current_record.b_games,
                                "match_format": current_record.match.match_format.value
                                if current_record.match.match_format
                                else "games_9",
                            },
                        },
                    }
                ), 400

        # 執行更新
        updated_record = MatchRecordService.update_match_record(
            record_id, validated_data
        )

        return jsonify(
            {
                "message": "比賽記錄已成功更新。",
                "match_record": response_schema.dump(updated_record),
            }
        ), 200

    except MarshmallowValidationError as err:
        return jsonify(
            {
                "error": "validation_error",
                "message": "輸入數據有誤。",
                "details": err.messages,
            }
        ), 400
    except ValidationError as e:
        # 🔧 修改：提供更詳細的分數驗證錯誤信息
        return jsonify(
            {
                "error": "score_validation_error",
                "message": str(e),
                "details": {"score_validation": [str(e)]},
                "score_info": {
                    "a_games": json_data.get("a_games"),
                    "b_games": json_data.get("b_games"),
                    "match_format": json_data.get("match_format"),
                },
            }
        ), 400
    except AppException as e:
        return jsonify(
            e.to_dict() if hasattr(e, "to_dict") else {"error": str(e)}
        ), getattr(e, "status_code", 400)
    except Exception as e:
        current_app.logger.error(
            f"更新比賽記錄 ID {record_id} 時發生錯誤: {e}", exc_info=True
        )
        return jsonify(
            {"error": "server_error", "message": "更新比賽記錄時發生錯誤。"}
        ), 500


@api_bp.route("/match-records/<int:record_id>", methods=["GET"])
def get_single_match_record(record_id):
    """
    根據 ID 獲取單場比賽記錄的詳細資訊。
    🔧 修改：增加分數驗證狀態信息
    """
    try:
        record = MatchRecordService.get_match_record_by_id(record_id)
        if not record:
            return jsonify(
                {"error": "not_found", "message": "找不到指定的比賽記錄。"}
            ), 404

        # 🔧 新增：在返回數據中包含分數驗證信息
        response_data = response_schema.dump(record)

        # 加入分數驗證狀態
        if record.match and record.match.match_format:
            match_format = record.match.match_format.value
            is_valid, _ = MatchRecordService._validate_match_score(
                record.a_games, record.b_games, match_format
            )
            response_data["score_validation"] = {
                "is_valid": is_valid,
                "games_to_win": MatchRecordService._get_games_to_win(match_format),
                "match_format": match_format,
            }

        return jsonify({"match_record": response_data}), 200
    except Exception as e:
        current_app.logger.error(
            f"獲取比賽記錄 ID {record_id} 時發生錯誤: {e}", exc_info=True
        )
        return jsonify(
            {"error": "server_error", "message": "獲取記錄時發生錯誤。"}
        ), 500


# 🔧 新增：分數驗證輔助端點（可選）
@api_bp.route("/match-records/validate-score", methods=["POST"])
def validate_match_score():
    """
    🔧 新增：專門用於前端實時分數驗證的端點
    這是一個輕量級端點，只驗證分數而不執行任何數據庫操作
    """
    json_data = request.get_json()
    if not json_data:
        return jsonify(
            {"error": "missing_json", "message": "缺少 JSON 請求內容。"}
        ), 400

    try:
        # 驗證必要字段
        required_fields = ["a_games", "b_games", "match_format"]
        missing_fields = [field for field in required_fields if field not in json_data]

        if missing_fields:
            return jsonify(
                {
                    "error": "missing_fields",
                    "message": f"缺少必要字段: {', '.join(missing_fields)}",
                    "required_fields": required_fields,
                }
            ), 400

        # 驗證分數
        is_valid, error_msg = MatchRecordService._validate_match_score(
            json_data["a_games"], json_data["b_games"], json_data["match_format"]
        )

        games_to_win = MatchRecordService._get_games_to_win(json_data["match_format"])

        # 計算預期結果
        predicted_outcome = None
        if is_valid:
            if (
                json_data["a_games"] >= games_to_win
                and json_data["a_games"] > json_data["b_games"]
            ):
                predicted_outcome = "WIN"
            elif (
                json_data["b_games"] >= games_to_win
                and json_data["b_games"] > json_data["a_games"]
            ):
                predicted_outcome = "LOSS"
            else:
                predicted_outcome = "PENDING"

        return jsonify(
            {
                "is_valid": is_valid,
                "message": "分數有效" if is_valid else error_msg,
                "score_info": {
                    "a_games": json_data["a_games"],
                    "b_games": json_data["b_games"],
                    "match_format": json_data["match_format"],
                    "games_to_win": games_to_win,
                    "predicted_side_a_outcome": predicted_outcome,
                },
            }
        ), 200

    except Exception as e:
        current_app.logger.error(f"驗證分數時發生錯誤: {e}", exc_info=True)
        return jsonify(
            {"error": "server_error", "message": "驗證分數時發生錯誤。"}
        ), 500


# 其他現有端點保持不變...
@api_bp.route("/match-records", methods=["GET"])
def get_all_match_records():
    """獲取比賽記錄列表，支援篩選、排序和分頁。"""
    try:
        # 驗證查詢參數
        try:
            query_params = query_schema.load(request.args)
        except MarshmallowValidationError as err:
            return jsonify(
                {
                    "error": "validation_error",
                    "message": "查詢參數有誤。",
                    "details": err.messages,
                }
            ), 400

        # 獲取記錄（可能包含分頁資訊）
        result = MatchRecordService.get_all_match_records(query_params)

        # 檢查是否有分頁資訊
        if isinstance(result, dict) and "items" in result:
            # 有分頁的回應
            return jsonify(
                {
                    "match_records": responses_schema.dump(result["items"]),
                    "pagination": {
                        "total": result["total"],
                        "page": result["page"],
                        "per_page": result["per_page"],
                        "pages": result["pages"],
                        "has_next": result["has_next"],
                        "has_prev": result["has_prev"],
                    },
                }
            ), 200
        else:
            # 沒有分頁的回應（向後相容）
            return jsonify({"match_records": responses_schema.dump(result)}), 200

    except Exception as e:
        current_app.logger.error(f"獲取比賽記錄列表時發生錯誤: {e}", exc_info=True)
        return jsonify(
            {"error": "server_error", "message": "獲取列表時發生錯誤。"}
        ), 500


@api_bp.route("/match-records/<int:record_id>", methods=["DELETE"])
@jwt_required()
def delete_match_record(record_id):
    """刪除一場比賽記錄，並觸發相關球員評分的重新計算。"""
    record = MatchRecordService.get_match_record_by_id(record_id)
    if not record:
        return jsonify(
            {"error": "not_found", "message": "找不到要刪除的比賽記錄。"}
        ), 404

    try:
        MatchRecordService.delete_match_record(record)
        return jsonify({"message": "比賽記錄已成功刪除，相關球員評分已更新。"}), 200
    except AppException as e:
        return jsonify(
            e.to_dict() if hasattr(e, "to_dict") else {"error": str(e)}
        ), getattr(e, "status_code", 400)
    except Exception as e:
        current_app.logger.error(
            f"刪除比賽記錄 ID {record_id} 時發生錯誤: {e}", exc_info=True
        )
        return jsonify(
            {"error": "server_error", "message": "刪除比賽記錄時發生錯誤。"}
        ), 500


@api_bp.route("/match-records/statistics", methods=["GET"])
def get_match_statistics():
    """獲取比賽統計資訊。"""
    try:
        # 驗證查詢參數（重用查詢 schema）
        try:
            query_params = query_schema.load(request.args)
        except MarshmallowValidationError as err:
            return jsonify(
                {
                    "error": "validation_error",
                    "message": "查詢參數有誤。",
                    "details": err.messages,
                }
            ), 400

        # 獲取統計資訊
        statistics = MatchRecordService.get_match_statistics(query_params)

        return jsonify({"statistics": statistics, "filters_applied": query_params}), 200

    except Exception as e:
        current_app.logger.error(f"獲取比賽統計時發生錯誤: {e}", exc_info=True)
        return jsonify(
            {"error": "server_error", "message": "獲取統計資訊時發生錯誤。"}
        ), 500


@api_bp.route("/match-records/recent", methods=["GET"])
def get_recent_matches():
    """獲取最近的比賽記錄（簡化版本）"""
    try:
        limit = min(int(request.args.get("limit", 10)), 50)  # 限制最多50筆

        result = MatchRecordService.get_all_match_records(
            {
                "per_page": limit,
                "page": 1,
                "sort_by": "match_date",
                "sort_order": "desc",
            }
        )

        # 使用基本 schema 減少資料量
        if isinstance(result, dict) and "items" in result:
            matches = [record.match for record in result["items"] if record.match]
            return jsonify(
                {"recent_matches": [basic_schema.dump(match) for match in matches]}
            ), 200
        else:
            matches = [record.match for record in result if record.match]
            return jsonify(
                {"recent_matches": [basic_schema.dump(match) for match in matches]}
            ), 200

    except Exception as e:
        current_app.logger.error(f"獲取最近比賽時發生錯誤: {e}", exc_info=True)
        return jsonify(
            {"error": "server_error", "message": "獲取最近比賽時發生錯誤。"}
        ), 500


@api_bp.route("/match-records/player/<int:player_id>", methods=["GET"])
def get_player_match_history(player_id):
    """獲取特定球員的比賽歷史"""
    try:
        # 驗證查詢參數
        try:
            query_params = query_schema.load(request.args)
        except MarshmallowValidationError as err:
            return jsonify(
                {
                    "error": "validation_error",
                    "message": "查詢參數有誤。",
                    "details": err.messages,
                }
            ), 400

        # 強制設定 player_id
        query_params["player_id"] = player_id

        result = MatchRecordService.get_all_match_records(query_params)

        if isinstance(result, dict) and "items" in result:
            return jsonify(
                {
                    "match_records": responses_schema.dump(result["items"]),
                    "pagination": {
                        "total": result["total"],
                        "page": result["page"],
                        "per_page": result["per_page"],
                        "pages": result["pages"],
                        "has_next": result["has_next"],
                        "has_prev": result["has_prev"],
                    },
                    "player_id": player_id,
                }
            ), 200
        else:
            return jsonify(
                {"match_records": responses_schema.dump(result), "player_id": player_id}
            ), 200

    except Exception as e:
        current_app.logger.error(
            f"獲取球員 {player_id} 比賽歷史時發生錯誤: {e}", exc_info=True
        )
        return jsonify(
            {"error": "server_error", "message": "獲取球員比賽歷史時發生錯誤。"}
        ), 500
