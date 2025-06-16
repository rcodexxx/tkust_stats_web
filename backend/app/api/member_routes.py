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
from sqlalchemy import func, or_
from sqlalchemy.orm import joinedload

from ..config import RatingCalculationConfig
from ..extensions import db
from ..models import Member, Organization
from ..models.enums import GuestRoleEnum
from ..schemas.member_schemas import (
    GuestCreateResponseSchema,
    GuestCreateSchema,
    GuestListResponseSchema,
    GuestQuerySchema,
    GuestUpdateSchema,
    LeaderboardMemberSchema,
    LeaderboardQuerySchema,
    MemberComparisonSchema,
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

# 排行榜 Schemas
leaderboard_query_schema = LeaderboardQuerySchema()
leaderboard_schema = LeaderboardMemberSchema(many=True)
member_comparison_schema = MemberComparisonSchema()

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
    try:
        # 使用新的排行榜邏輯，但返回舊格式
        members = Member.get_ranking_by_conservative_score(
            limit=50, include_guests=True
        ).all()
        return jsonify(leaderboard_schema.dump(members)), 200
    except Exception as e:
        return handle_server_error(e, "獲取排行榜時發生錯誤", "_get_leaderboard_legacy")


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


# ===== 排行榜與評分系統 =====
@api_bp.route("/members/leaderboard", methods=["GET"])
@jwt_required(optional=True)
def get_leaderboard():
    """
    獲取四維度評分排行榜（修正版本）
    """
    try:
        # 驗證查詢參數
        args = leaderboard_query_schema.load(request.args)

        # 獲取排行榜數據
        query = Member.get_ranking_by_conservative_score(
            limit=args.get("limit", 50), include_guests=args.get("include_guests", True)
        )

        # 額外篩選條件
        if args.get("organization_id"):
            query = query.filter(Member.organization_id == args["organization_id"])

        # 執行查詢
        members = query.all()

        # 應用層篩選
        if args.get("experience_level"):
            members = [
                m for m in members if m.experience_level == args["experience_level"]
            ]

        # 計算正確的比賽場數
        members = _enrich_members_with_match_counts(members)

        # 應用最少比賽場次篩選
        if args.get("min_matches", 0) > 0:
            min_matches = args["min_matches"]
            members = [
                m
                for m in members
                if getattr(m, "_calculated_match_count", 0) >= min_matches
            ]

        # 重新排序（因為篩選可能改變順序）
        members.sort(key=lambda m: m.conservative_score, reverse=True)

        # 添加排名資訊
        for i, member in enumerate(members, 1):
            member._rank = i

        # 獲取系統統計
        statistics = _get_system_statistics()

        return jsonify(
            {
                "message": "排行榜獲取成功",
                "data": leaderboard_schema.dump(members),
                "total": len(members),
                "statistics": statistics,
                "config": Member.get_trueskill_config(),
                "query_params": args,
            }
        ), 200

    except ValidationError as err:
        return handle_validation_error(err, "查詢參數錯誤")
    except Exception as e:
        return handle_server_error(e, "獲取排行榜時發生錯誤", "get_leaderboard")


@api_bp.route("/members/<int:member_id>/compare/<int:other_id>", methods=["GET"])
@jwt_required(optional=True)
def compare_members(member_id, other_id):
    """
    比較兩位球員的四維度評分
    """
    try:
        member1 = Member.query.get_or_404(member_id)
        member2 = Member.query.get_or_404(other_id)

        comparison = member1.compare_skill_with(member2)

        return jsonify(
            {
                "message": "比較完成",
                "comparison": member_comparison_schema.dump(comparison),
                "member1": {
                    "id": member1.id,
                    "name": member1.display_name,
                    "official_score": round(member1.conservative_score, 2),
                    "four_dimensions": member1.get_four_dimension_scores(),
                },
                "member2": {
                    "id": member2.id,
                    "name": member2.display_name,
                    "official_score": round(member2.conservative_score, 2),
                    "four_dimensions": member2.get_four_dimension_scores(),
                },
            }
        ), 200

    except Exception as e:
        return handle_server_error(e, "比較球員時發生錯誤", "compare_members")


@api_bp.route("/members/trueskill-stats", methods=["GET"])
@jwt_required(optional=True)
def get_trueskill_statistics():
    """
    獲取 TrueSkill 四維度評分系統統計信息
    """
    try:
        statistics = _get_system_statistics()

        return jsonify(
            {
                "message": "統計信息獲取成功",
                "statistics": statistics,
                "config": Member.get_trueskill_config(),
            }
        ), 200

    except Exception as e:
        return handle_server_error(
            e, "獲取統計信息時發生錯誤", "get_trueskill_statistics"
        )


def _get_system_statistics():
    """獲取系統統計信息（修復版本）"""
    try:
        # 基本統計 - 使用原始 SQL 避免 join 問題
        basic_stats = (
            db.session.query(
                func.avg(Member.mu).label("avg_mu"),
                func.avg(Member.sigma).label("avg_sigma"),
                func.avg(
                    Member.mu
                    - RatingCalculationConfig.TRUESKILL_CONSERVATIVE_K * Member.sigma
                ).label("avg_conservative"),
                func.min(
                    Member.mu
                    - RatingCalculationConfig.TRUESKILL_CONSERVATIVE_K * Member.sigma
                ).label("min_score"),
                func.max(
                    Member.mu
                    - RatingCalculationConfig.TRUESKILL_CONSERVATIVE_K * Member.sigma
                ).label("max_score"),
                func.count(Member.id).label("total_players"),
            )
            .filter(
                # 簡化活躍條件，避免複雜的 join
                db.or_(
                    # 訪客：未離隊
                    db.and_(Member.is_guest == True, Member.leaved_date.is_(None)),
                    # 正式會員：有 user_id 且未離隊（這裡假設有 user_id 的都是活躍的）
                    db.and_(
                        Member.is_guest == False,
                        Member.user_id.isnot(None),
                        Member.leaved_date.is_(None),
                    ),
                )
            )
            .first()
        )

        # 獲取活躍會員來計算分布（使用修復後的方法）
        active_members = Member.get_active_players(include_guests=True).all()

        if not active_members:
            return {
                "basic": {
                    "total_active_players": 0,
                    "average_mu": 0,
                    "average_sigma": 0,
                    "average_conservative_score": 0,
                    "score_range": {"min": 0, "max": 0},
                },
                "experience_distribution": {},
                "stability_distribution": {},
                "system_health": {},
            }

        # 經驗等級分布
        experience_distribution = {}
        for level in ["新手", "初級", "中級", "高級", "資深"]:
            level_count = len(
                [m for m in active_members if m.experience_level == level]
            )
            experience_distribution[level] = level_count

        # 穩定度分布
        stability_ranges = {
            "excellent": len([m for m in active_members if m.consistency_rating >= 80]),
            "good": len([m for m in active_members if 60 <= m.consistency_rating < 80]),
            "average": len(
                [m for m in active_members if 40 <= m.consistency_rating < 60]
            ),
            "poor": len([m for m in active_members if m.consistency_rating < 40]),
        }

        # 系統健康指標
        total_confidence = sum(m.rating_confidence for m in active_members)
        avg_confidence = total_confidence / len(active_members) if active_members else 0
        experienced_count = len([m for m in active_members if m.is_experienced_player])

        return {
            "basic": {
                "total_active_players": int(basic_stats.total_players or 0),
                "average_mu": round(float(basic_stats.avg_mu or 0), 2),
                "average_sigma": round(float(basic_stats.avg_sigma or 0), 2),
                "average_conservative_score": round(
                    float(basic_stats.avg_conservative or 0), 2
                ),
                "score_range": {
                    "min": round(float(basic_stats.min_score or 0), 2),
                    "max": round(float(basic_stats.max_score or 0), 2),
                },
            },
            "experience_distribution": experience_distribution,
            "stability_distribution": stability_ranges,
            "system_health": {
                "avg_confidence": round(avg_confidence, 2),
                "experienced_players": experienced_count,
                "new_players": len(active_members) - experienced_count,
                "guest_count": len([m for m in active_members if m.is_guest]),
                "member_count": len([m for m in active_members if not m.is_guest]),
            },
        }

    except Exception as e:
        current_app.logger.error(f"統計計算錯誤: {e}", exc_info=True)
        # 返回空統計避免 API 完全失敗
        return {
            "basic": {
                "total_active_players": 0,
                "average_mu": 0,
                "average_sigma": 0,
                "average_conservative_score": 0,
                "score_range": {"min": 0, "max": 0},
            },
            "experience_distribution": {},
            "stability_distribution": {},
            "system_health": {},
        }


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


# ===== 系統健康檢查 =====
@api_bp.route("/members/system-health", methods=["GET"])
@jwt_required()
def get_system_health():
    """
    獲取系統健康狀態
    管理員用於監控系統狀態
    """
    try:
        health_data = {
            "timestamp": db.func.now(),
            "database": {
                "total_members": Member.query.count(),
                "active_members": Member.query.filter(Member.is_active == True).count(),
                "guests": Member.query.filter(Member.is_guest == True).count(),
                "regular_members": Member.query.filter(
                    Member.is_guest == False
                ).count(),
            },
            "rating_system": {
                "config": Member.get_trueskill_config(),
                "score_distribution": _get_score_distribution(),
            },
        }

        return jsonify(
            {
                "message": "系統健康檢查完成",
                "health": health_data,
            }
        ), 200

    except Exception as e:
        return handle_server_error(e, "系統健康檢查失敗", "get_system_health")


def _get_score_distribution():
    """獲取評分分佈"""
    try:
        active_members = Member.get_active_players(include_guests=True).all()

        if not active_members:
            return {}

        scores = [m.conservative_score for m in active_members]
        scores.sort()

        n = len(scores)
        if n == 0:
            return {}

        return {
            "min": round(min(scores), 2),
            "max": round(max(scores), 2),
            "avg": round(sum(scores) / n, 2),
            "median": round(scores[n // 2], 2),
            "quartiles": {
                "q1": round(scores[n // 4], 2) if n >= 4 else round(scores[0], 2),
                "q2": round(scores[n // 2], 2),
                "q3": round(scores[3 * n // 4], 2) if n >= 4 else round(scores[-1], 2),
            },
            "count": n,
        }
    except Exception as e:
        current_app.logger.error(f"評分分布計算錯誤: {e}", exc_info=True)
        return {}


def _calculate_member_match_counts(member_ids=None):
    """
    計算球員的正確比賽場數

    Args:
        member_ids: 指定計算的球員ID列表，None則計算所有球員

    Returns:
        dict: {member_id: match_count}
    """
    try:
        from ..models import MatchRecord

        # 基礎查詢
        query = (
            db.session.query(MatchRecord.player1_id.label("player_id"))
            .union_all(
                db.session.query(MatchRecord.player2_id.label("player_id")).filter(
                    MatchRecord.player2_id.isnot(None)
                )
            )
            .union_all(db.session.query(MatchRecord.player3_id.label("player_id")))
            .union_all(
                db.session.query(MatchRecord.player4_id.label("player_id")).filter(
                    MatchRecord.player4_id.isnot(None)
                )
            )
        )

        # 如果指定了球員ID，進行篩選
        if member_ids:
            query = query.filter(
                or_(
                    MatchRecord.player1_id.in_(member_ids),
                    MatchRecord.player2_id.in_(member_ids),
                    MatchRecord.player3_id.in_(member_ids),
                    MatchRecord.player4_id.in_(member_ids),
                )
            )

        # 計算每個球員的比賽場次
        subquery = query.subquery()
        match_counts = (
            db.session.query(subquery.c.player_id, func.count().label("match_count"))
            .group_by(subquery.c.player_id)
            .all()
        )

        # 轉換為字典
        return {player_id: count for player_id, count in match_counts if player_id}

    except Exception as e:
        current_app.logger.error(f"計算比賽場數錯誤: {e}", exc_info=True)
        return {}


def _enrich_members_with_match_counts(members):
    """
    為球員列表添加正確的比賽場數

    Args:
        members: 球員列表

    Returns:
        list: 包含正確比賽場數的球員列表
    """
    if not members:
        return members

    # 獲取所有球員ID
    member_ids = [m.id for m in members]

    # 計算比賽場數
    match_counts = _calculate_member_match_counts(member_ids)

    # 更新球員數據
    enriched_members = []
    for member in members:
        # 創建一個臨時屬性來存儲正確的比賽場數
        member._calculated_match_count = match_counts.get(member.id, 0)
        enriched_members.append(member)

    return enriched_members


@api_bp.route("/members/recalculate-match-counts", methods=["POST"])
@jwt_required()
def recalculate_match_counts():
    """
    重新計算所有球員的比賽場數（管理員功能）
    """
    try:
        # 檢查權限（可選）
        current_user_id = get_current_user_id()
        # 這裡可以添加管理員權限檢查

        # 獲取所有活躍球員
        all_members = Member.get_active_players(include_guests=True).all()

        # 計算比賽場數
        match_counts = _calculate_member_match_counts()

        # 統計結果
        updated_count = 0
        total_matches = 0

        for member in all_members:
            correct_count = match_counts.get(member.id, 0)
            total_matches += correct_count
            updated_count += 1

        current_app.logger.info(
            f"重新計算了 {updated_count} 位球員的比賽場數，總計 {total_matches} 場比賽"
        )

        return jsonify(
            {
                "message": "比賽場數重新計算完成",
                "statistics": {
                    "updated_members": updated_count,
                    "total_matches": total_matches,
                    "match_counts_sample": dict(list(match_counts.items())[:5]),
                },
            }
        ), 200

    except Exception as e:
        return handle_server_error(
            e, "重新計算比賽場數失敗", "recalculate_match_counts"
        )
