# backend/app/api/leaderboard_routes.py
"""
排行榜相關的 API 路由 - 修復版本
"""

from flask import current_app, jsonify, request
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError

# 使用正確的 leaderboard_schemas
from ..schemas.leaderboard_schemas import (
    LeaderboardPlayerSchema,
    LeaderboardQuerySchema,
    LeaderboardStatisticsSchema,
    PlayerComparisonSchema,
)
from ..services.leaderboard_service import LeaderboardService
from ..tools.exceptions import AppException
from . import api_bp

# Schema 實例
leaderboard_schema = LeaderboardPlayerSchema(many=True)
leaderboard_query_schema = LeaderboardQuerySchema()
player_comparison_schema = PlayerComparisonSchema()
statistics_schema = LeaderboardStatisticsSchema()


def handle_validation_error(error: ValidationError, message: str = "輸入數據有誤"):
    """統一處理驗證錯誤"""
    return jsonify(
        {
            "error": "validation_error",
            "message": message,
            "details": error.messages,
        }
    ), 400


def handle_server_error(error: Exception, message: str, operation: str = ""):
    """統一處理伺服器錯誤"""
    current_app.logger.error(f"Error in {operation}: {error}", exc_info=True)
    return jsonify({"error": "server_error", "message": message}), 500


@api_bp.route("/leaderboard", methods=["GET"])
@jwt_required(optional=True)
def get_leaderboard():
    """
    獲取排行榜數據 - 唯一的排行榜端點
    """
    try:
        current_app.logger.info(f"[LeaderboardAPI] 收到請求，參數: {request.args}")

        # 驗證查詢參數
        query_params = request.args.to_dict()

        # 使用 LeaderboardQuerySchema 進行驗證
        try:
            validated_params = leaderboard_query_schema.load(query_params)
        except ValidationError as err:
            return handle_validation_error(err, "查詢參數格式錯誤")

        # 額外的類型轉換（URL 參數都是字符串）
        for key in ["limit", "page", "per_page", "organization_id", "min_matches"]:
            if key in query_params and query_params[key]:
                try:
                    validated_params[key] = int(query_params[key])
                except ValueError:
                    current_app.logger.warning(
                        f"無法轉換參數 {key}: {query_params[key]}"
                    )

        for key in ["include_guests", "include_inactive"]:
            if key in query_params:
                validated_params[key] = query_params[key].lower() == "true"

        if "min_win_rate" in query_params and query_params["min_win_rate"]:
            try:
                validated_params["min_win_rate"] = float(query_params["min_win_rate"])
            except ValueError:
                current_app.logger.warning(
                    f"無法轉換 min_win_rate: {query_params['min_win_rate']}"
                )

        current_app.logger.info(f"[LeaderboardAPI] 驗證後參數: {validated_params}")

        # 使用 LeaderboardService 獲取數據
        result = LeaderboardService.get_leaderboard(validated_params)

        current_app.logger.info(
            f"[LeaderboardAPI] Service 返回數據類型: {type(result['data'])}"
        )
        current_app.logger.info(f"[LeaderboardAPI] 數據數量: {len(result['data'])}")

        # 調試：檢查 Service 是否正確設置了統計屬性
        if result["data"]:
            first_member = result["data"][0]
            current_app.logger.info(
                f"[LeaderboardAPI] 第一個球員: {first_member.display_name}"
            )

            # 檢查 LeaderboardService 設置的統計屬性
            stats_attrs = ["_wins", "_losses", "_total_matches", "_win_rate", "_rank"]
            for attr in stats_attrs:
                if hasattr(first_member, attr):
                    value = getattr(first_member, attr)
                    current_app.logger.info(f"[LeaderboardAPI] ✅ {attr}: {value}")
                else:
                    current_app.logger.warning(f"[LeaderboardAPI] ❌ 缺少屬性: {attr}")

        # 序列化數據
        current_app.logger.info("[LeaderboardAPI] 開始序列化數據...")
        try:
            # 使用 LeaderboardPlayerSchema 序列化
            serialized_data = leaderboard_schema.dump(result["data"])
            result["data"] = serialized_data

            current_app.logger.info(
                f"[LeaderboardAPI] ✅ 序列化成功，數量: {len(serialized_data)}"
            )

            # 檢查序列化後的數據
            if serialized_data:
                first_serialized = serialized_data[0]
                current_app.logger.info(
                    f"[LeaderboardAPI] 序列化後字段: {list(first_serialized.keys())}"
                )

                # 檢查關鍵統計字段
                key_fields = ["win_rate", "total_matches", "wins", "losses", "rank"]
                for field in key_fields:
                    if field in first_serialized:
                        current_app.logger.info(
                            f"[LeaderboardAPI] ✅ {field}: {first_serialized[field]}"
                        )
                    else:
                        current_app.logger.warning(
                            f"[LeaderboardAPI] ❌ 序列化後缺少: {field}"
                        )

        except Exception as serial_error:
            current_app.logger.error(
                f"[LeaderboardAPI] 序列化失敗: {serial_error}", exc_info=True
            )
            raise serial_error

        return jsonify({"message": "排行榜獲取成功", **result}), 200

    except ValidationError as err:
        return handle_validation_error(err, "查詢參數錯誤")
    except Exception as e:
        current_app.logger.error(f"[LeaderboardAPI] 獲取排行榜失敗: {e}", exc_info=True)
        return handle_server_error(e, "獲取排行榜時發生錯誤", "get_leaderboard")


@api_bp.route("/leaderboard/compare/<int:member1_id>/<int:member2_id>", methods=["GET"])
@jwt_required(optional=True)
def compare_players(member1_id, member2_id):
    """
    比較兩位球員
    """
    try:
        if member1_id == member2_id:
            return jsonify(
                {"error": "validation_error", "message": "不能比較相同的球員"}
            ), 400

        result = LeaderboardService.compare_players(member1_id, member2_id)

        # 使用 PlayerComparisonSchema 序列化比較結果
        if "comparison" in result:
            result["comparison"] = player_comparison_schema.dump(result["comparison"])

        return jsonify({"message": "球員比較完成", **result}), 200

    except AppException as e:
        return jsonify(e.to_dict()), e.status_code
    except Exception as e:
        return handle_server_error(e, "比較球員時發生錯誤", "compare_players")


@api_bp.route("/leaderboard/statistics", methods=["GET"])
@jwt_required(optional=True)
def get_leaderboard_statistics():
    """
    獲取排行榜統計信息
    """
    try:
        statistics = LeaderboardService.get_statistics()

        # 使用 LeaderboardStatisticsSchema 序列化統計數據
        serialized_stats = statistics_schema.dump(statistics)

        return jsonify(
            {"message": "統計信息獲取成功", "statistics": serialized_stats}
        ), 200

    except Exception as e:
        return handle_server_error(
            e, "獲取統計信息時發生錯誤", "get_leaderboard_statistics"
        )


@api_bp.route("/leaderboard/<int:member_id>/match-stats", methods=["GET"])
@jwt_required(optional=True)
def get_member_match_stats(member_id):
    """
    獲取單個球員的詳細比賽統計
    """
    try:
        from ..models import Member

        # 驗證球員存在
        member = Member.query.get_or_404(member_id)

        # 使用 LeaderboardService 的統計計算方法
        stats = LeaderboardService._calculate_match_statistics([member_id])
        last_match_dates = LeaderboardService._get_last_match_dates([member_id])

        member_stats = stats.get(
            member_id, {"wins": 0, "losses": 0, "total_matches": 0, "win_rate": 0.0}
        )

        result = {
            "member_id": member_id,
            "member_name": member.display_name,
            "match_statistics": member_stats,
            "last_match_date": last_match_dates.get(member_id),
            "four_dimensions": member.get_four_dimension_scores(),
            "rating_summary": member.get_rating_summary(),
        }

        return jsonify({"message": "球員統計獲取成功", **result}), 200

    except Exception as e:
        return handle_server_error(
            e, "獲取球員統計時發生錯誤", "get_member_match_stats"
        )


# 調試端點（開發用）
@api_bp.route("/leaderboard/debug", methods=["GET"])
@jwt_required(optional=True)
def debug_leaderboard():
    """
    調試用端點 - 檢查序列化過程
    """
    try:
        current_app.logger.info("[DEBUG] 開始調試排行榜序列化")

        # 獲取少量數據進行調試
        result = LeaderboardService.get_leaderboard({"limit": 3})

        debug_info = {
            "service_data_count": len(result["data"]),
            "service_data_type": str(type(result["data"])),
            "members_info": [],
        }

        # 檢查每個 Member 對象
        for i, member in enumerate(result["data"][:3]):  # 只檢查前3個
            member_info = {
                "index": i,
                "id": member.id,
                "display_name": member.display_name,
                "type": str(type(member)),
                "attributes": {},
            }

            # 檢查統計屬性
            for attr in ["_wins", "_losses", "_total_matches", "_win_rate", "_rank"]:
                if hasattr(member, attr):
                    member_info["attributes"][attr] = getattr(member, attr)
                else:
                    member_info["attributes"][attr] = "❌ 缺少"

            debug_info["members_info"].append(member_info)

        # 嘗試序列化
        try:
            serialized = leaderboard_schema.dump(result["data"])
            debug_info["serialization_success"] = True
            debug_info["serialized_count"] = len(serialized)

            if serialized:
                debug_info["first_serialized_keys"] = list(serialized[0].keys())
                debug_info["first_serialized_win_rate"] = serialized[0].get(
                    "win_rate", "❌ 缺少"
                )

        except Exception as e:
            debug_info["serialization_success"] = False
            debug_info["serialization_error"] = str(e)

        return jsonify({"message": "調試信息", "debug_info": debug_info}), 200

    except Exception as e:
        return jsonify({"error": "調試失敗", "message": str(e)}), 500
