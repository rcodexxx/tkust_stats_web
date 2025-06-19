# backend/app/services/leaderboard_service.py
"""
排行榜服務層 - 重構版本，基於實際的數據庫結構
"""

from datetime import datetime, timedelta
from typing import Dict, List

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import joinedload

from ..config import RatingCalculationConfig
from ..extensions import db
from ..models import Match, MatchRecord, Member, Organization
from ..models.enums import MatchOutcomeEnum


class LeaderboardService:
    """排行榜服務類 - 重構版本"""

    @staticmethod
    def get_leaderboard(query_params: dict) -> Dict:
        """
        獲取排行榜數據

        Args:
            query_params: 查詢參數字典

        Returns:
            包含排行榜數據和統計信息的字典
        """
        # 解析查詢參數
        limit = query_params.get("limit", 50)
        page = query_params.get("page", 1)
        per_page = query_params.get("per_page", 50)
        include_guests = query_params.get("include_guests", True)
        include_inactive = query_params.get("include_inactive", False)

        # 構建基礎查詢
        members_query = LeaderboardService._build_base_query(
            include_guests=include_guests, include_inactive=include_inactive
        )

        # 應用篩選條件
        members_query = LeaderboardService._apply_filters(members_query, query_params)

        # 獲取成員列表
        all_members = members_query.all()

        # 添加比賽統計
        enriched_members = LeaderboardService._enrich_members_with_match_stats(
            all_members
        )

        # 應用進階篩選（需要計算後的數據）
        filtered_members = LeaderboardService._apply_advanced_filters(
            enriched_members, query_params
        )

        # 排序
        sorted_members = LeaderboardService._sort_members(
            filtered_members,
            query_params.get("sort_by", "score"),
            query_params.get("sort_order", "desc"),
        )

        # 添加排名
        for i, member in enumerate(sorted_members, 1):
            member._rank = i

        # 分頁
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_members = sorted_members[start_idx:end_idx]

        # 獲取統計信息
        statistics = LeaderboardService.get_statistics()

        return {
            "data": paginated_members,
            "total": len(sorted_members),
            "page": page,
            "per_page": per_page,
            "total_pages": (len(sorted_members) + per_page - 1) // per_page,
            "statistics": statistics,
            "config": Member.get_trueskill_config(),
            "query_params": query_params,
        }

    @staticmethod
    def _build_base_query(include_guests: bool = True, include_inactive: bool = False):
        """構建基礎查詢"""
        query = db.session.query(Member).options(
            joinedload(Member.user), joinedload(Member.organization)
        )

        # 是否包含訪客
        if not include_guests:
            query = query.filter(Member.is_guest == False)

        # 是否包含非活躍成員
        if not include_inactive:
            # 活躍條件：未離隊且（是訪客或有關聯用戶）
            query = query.filter(
                Member.leaved_date.is_(None),
                or_(
                    Member.is_guest == True,
                    and_(Member.is_guest == False, Member.user_id.isnot(None)),
                ),
            )

        return query

    @staticmethod
    def _apply_filters(query, params: dict):
        """應用基本篩選條件"""
        # 組織篩選
        if params.get("organization_id"):
            query = query.filter(Member.organization_id == params["organization_id"])
        elif params.get("organization_ids"):
            query = query.filter(Member.organization_id.in_(params["organization_ids"]))

        # 經驗等級篩選
        if params.get("experience_level"):
            # 由於 experience_level 是計算屬性，這裡需要通過 sigma 值來篩選
            level_map = {
                "新手": (7.0, float("inf")),
                "初級": (5.0, 7.0),
                "中級": (3.0, 5.0),
                "高級": (2.0, 3.0),
                "資深": (0, 2.0),
            }
            if params["experience_level"] in level_map:
                min_sigma, max_sigma = level_map[params["experience_level"]]
                query = query.filter(
                    Member.sigma >= min_sigma, Member.sigma < max_sigma
                )

        # 加入時間篩選
        if params.get("joined_after"):
            query = query.filter(Member.joined_date >= params["joined_after"])

        return query

    @staticmethod
    def _enrich_members_with_match_stats(members: List[Member]) -> List[Member]:
        """
        為成員添加比賽統計數據 - 簡化版本

        只設置必要的屬性，不搞複雜的別名
        """
        if not members:
            return members

        member_ids = [m.id for m in members]
        print(f"🔍 [DEBUG] 正在為 {len(member_ids)} 個球員計算比賽統計")

        # 獲取比賽統計
        match_stats = LeaderboardService._calculate_match_statistics(member_ids)

        # 獲取最近比賽日期
        last_match_dates = LeaderboardService._get_last_match_dates(member_ids)

        # 🔧 簡化：只設置必要的屬性
        for member in members:
            stats = match_stats.get(
                member.id, {"wins": 0, "losses": 0, "total_matches": 0, "win_rate": 0.0}
            )

            member._wins = stats["wins"]
            member._losses = stats["losses"]
            member._total_matches = stats["total_matches"]
            member._win_rate = stats["win_rate"]
            member._last_match_date = last_match_dates.get(member.id)

            # 🔍 調試輸出
            if stats["total_matches"] > 0:
                print(
                    f" ✅ {member.display_name}: {stats['wins']}勝{stats['losses']}敗 = {stats['total_matches']}場"
                )

        return members

    @staticmethod
    def _calculate_match_statistics(member_ids: List[int]) -> Dict:
        """
        計算球員的比賽統計 - 修復版本

        重點修復：
        1. 只計算有效的比賽記錄 (排除 PENDING)
        2. 正確判斷球員在哪一方
        3. 根據 side_a_outcome 正確計算勝負
        """
        if not member_ids:
            return {}

        print(f"🔍 [DEBUG] 開始計算 {len(member_ids)} 個球員的比賽統計")

        # 初始化統計字典
        stats = {member_id: {"wins": 0, "losses": 0} for member_id in member_ids}

        try:
            # 🔧 關鍵修復：查詢有效的比賽記錄，排除 PENDING
            matches = (
                db.session.query(MatchRecord)
                .filter(
                    and_(
                        # 球員篩選條件
                        or_(
                            MatchRecord.player1_id.in_(member_ids),
                            MatchRecord.player2_id.in_(member_ids),
                            MatchRecord.player3_id.in_(member_ids),
                            MatchRecord.player4_id.in_(member_ids),
                        ),
                        # 🔧 重要：只包含有效的比賽結果
                        MatchRecord.side_a_outcome.in_(
                            [MatchOutcomeEnum.WIN, MatchOutcomeEnum.LOSS]
                        ),
                    )
                )
                .all()
            )

            print(f"🔍 [DEBUG] 查詢到 {len(matches)} 場有效比賽記錄")

            # 🔧 修復：正確計算每場比賽的勝負
            for match in matches:
                # 確定哪些球員在 A 方 (player1, player2)
                side_a_players = []
                if match.player1_id and match.player1_id in member_ids:
                    side_a_players.append(match.player1_id)
                if match.player2_id and match.player2_id in member_ids:
                    side_a_players.append(match.player2_id)

                # 確定哪些球員在 B 方 (player3, player4)
                side_b_players = []
                if match.player3_id and match.player3_id in member_ids:
                    side_b_players.append(match.player3_id)
                if match.player4_id and match.player4_id in member_ids:
                    side_b_players.append(match.player4_id)

                # 🔧 重要：根據 side_a_outcome 判斷勝負
                if match.side_a_outcome == MatchOutcomeEnum.WIN:
                    # A 方獲勝
                    for player_id in side_a_players:
                        stats[player_id]["wins"] += 1
                    for player_id in side_b_players:
                        stats[player_id]["losses"] += 1

                elif match.side_a_outcome == MatchOutcomeEnum.LOSS:
                    # A 方失敗 (B 方獲勝)
                    for player_id in side_a_players:
                        stats[player_id]["losses"] += 1
                    for player_id in side_b_players:
                        stats[player_id]["wins"] += 1

            # 計算總場數和勝率
            for player_id, stat in stats.items():
                stat["total_matches"] = stat["wins"] + stat["losses"]
                stat["win_rate"] = (
                    round((stat["wins"] / stat["total_matches"]) * 100, 2)
                    if stat["total_matches"] > 0
                    else 0.0
                )

            # 🔍 調試輸出
            players_with_matches = sum(
                1 for stat in stats.values() if stat["total_matches"] > 0
            )
            total_match_participations = sum(
                stat["total_matches"] for stat in stats.values()
            )
            print(
                f"🔍 [DEBUG] 計算完成：{players_with_matches} 名球員有比賽記錄，總參與 {total_match_participations} 場次"
            )

        except Exception as e:
            print(f"❌ [ERROR] 計算比賽統計時發生錯誤: {e}")
            # 出錯時返回空統計
            for player_id in stats:
                stats[player_id] = {
                    "wins": 0,
                    "losses": 0,
                    "total_matches": 0,
                    "win_rate": 0.0,
                }

        return stats

    @staticmethod
    def _get_last_match_dates(member_ids: List[int]) -> Dict:
        """
        獲取球員最後比賽日期 - 修復版本
        """
        if not member_ids:
            return {}

        last_dates = {}

        try:
            # 🔧 修復：為每個球員查詢最後比賽日期
            for member_id in member_ids:
                # 查詢該球員參與的最新比賽
                last_match = (
                    db.session.query(Match.match_date)
                    .join(MatchRecord, MatchRecord.match_id == Match.id)
                    .filter(
                        or_(
                            MatchRecord.player1_id == member_id,
                            MatchRecord.player2_id == member_id,
                            MatchRecord.player3_id == member_id,
                            MatchRecord.player4_id == member_id,
                        ),
                        # 只考慮有效的比賽
                        MatchRecord.side_a_outcome.in_(
                            [MatchOutcomeEnum.WIN, MatchOutcomeEnum.LOSS]
                        ),
                    )
                    .order_by(desc(Match.match_date))
                    .first()
                )

                if last_match:
                    last_dates[member_id] = last_match.match_date

        except Exception as e:
            print(f"❌ [ERROR] 獲取最後比賽日期時發生錯誤: {e}")

        return last_dates

    @staticmethod
    def _apply_advanced_filters(members: List[Member], params: dict) -> List[Member]:
        """應用需要計算數據的進階篩選"""
        filtered = members

        # 最少比賽場次篩選
        if params.get("min_matches", 0) > 0:
            min_matches = params["min_matches"]
            filtered = [
                m for m in filtered if getattr(m, "_total_matches", 0) >= min_matches
            ]

        # 最低勝率篩選
        if params.get("min_win_rate") is not None:
            min_win_rate = params["min_win_rate"]
            filtered = [
                m for m in filtered if getattr(m, "_win_rate", 0) >= min_win_rate
            ]

        # 活躍時間篩選
        if params.get("active_since"):
            active_since = params["active_since"]
            filtered = [
                m
                for m in filtered
                if getattr(m, "_last_match_date", None)
                and m._last_match_date >= active_since
            ]

        return filtered

    @staticmethod
    def _sort_members(
        members: List[Member], sort_by: str, sort_order: str
    ) -> List[Member]:
        """排序成員列表"""
        reverse = sort_order == "desc"

        if sort_by == "win_rate":
            return sorted(
                members, key=lambda m: getattr(m, "_win_rate", 0), reverse=reverse
            )
        elif sort_by == "total_matches":
            return sorted(
                members, key=lambda m: getattr(m, "_total_matches", 0), reverse=reverse
            )
        elif sort_by == "wins":
            return sorted(
                members, key=lambda m: getattr(m, "_wins", 0), reverse=reverse
            )
        elif sort_by == "experience":
            exp_order = {"新手": 0, "初級": 1, "中級": 2, "高級": 3, "資深": 4}
            return sorted(
                members,
                key=lambda m: exp_order.get(m.experience_level, 0),
                reverse=reverse,
            )
        elif sort_by == "recent_activity":
            return sorted(
                members,
                key=lambda m: getattr(m, "_last_match_date", datetime.min),
                reverse=reverse,
            )
        elif sort_by == "join_date":
            return sorted(
                members, key=lambda m: m.joined_date or datetime.min, reverse=reverse
            )
        else:  # 預設按分數排序
            return sorted(members, key=lambda m: m.conservative_score, reverse=reverse)

    @staticmethod
    def compare_players(member1_id: int, member2_id: int) -> Dict:
        """比較兩位球員"""
        member1 = Member.query.get_or_404(member1_id)
        member2 = Member.query.get_or_404(member2_id)

        # 獲取比賽統計
        stats = LeaderboardService._calculate_match_statistics([member1_id, member2_id])

        # 技能比較
        comparison = member1.compare_skill_with(member2)

        return {
            "comparison": comparison,
            "member1": {
                "id": member1.id,
                "name": member1.display_name,
                "score": round(member1.conservative_score, 2),
                "four_dimensions": member1.get_four_dimension_scores(),
                "match_stats": stats.get(
                    member1_id,
                    {"wins": 0, "losses": 0, "total_matches": 0, "win_rate": 0.0},
                ),
            },
            "member2": {
                "id": member2.id,
                "name": member2.display_name,
                "score": round(member2.conservative_score, 2),
                "four_dimensions": member2.get_four_dimension_scores(),
                "match_stats": stats.get(
                    member2_id,
                    {"wins": 0, "losses": 0, "total_matches": 0, "win_rate": 0.0},
                ),
            },
        }

    @staticmethod
    def get_statistics() -> Dict:
        """獲取排行榜統計信息"""
        try:
            # 基本統計
            basic_stats = LeaderboardService._get_basic_statistics()

            # 分數分佈
            score_distribution = LeaderboardService._get_score_distribution()

            # 經驗分佈
            experience_distribution = LeaderboardService._get_experience_distribution()

            # 組織分佈
            organization_distribution = (
                LeaderboardService._get_organization_distribution()
            )

            # 活躍度統計
            activity_stats = LeaderboardService._get_activity_statistics()

            return {
                **basic_stats,
                "score_distribution": score_distribution,
                "experience_distribution": experience_distribution,
                "organization_distribution": organization_distribution,
                **activity_stats,
                "last_updated": datetime.now(),
                "data_freshness": "實時數據",
            }
        except Exception as e:
            import logging

            logging.error(f"獲取統計信息錯誤: {e}", exc_info=True)
            return LeaderboardService._get_default_statistics()

    @staticmethod
    def _get_basic_statistics() -> Dict:
        """獲取基本統計信息"""
        # 總人數統計
        total_members = Member.query.filter_by(is_guest=False).count()
        total_guests = Member.query.filter_by(is_guest=True).count()
        total_active = Member.query.filter(
            Member.leaved_date.is_(None),
            or_(
                Member.is_guest == True,
                and_(Member.is_guest == False, Member.user_id.isnot(None)),
            ),
        ).count()

        # 平均技能統計
        avg_stats = (
            db.session.query(
                func.avg(Member.mu).label("avg_mu"),
                func.avg(Member.sigma).label("avg_sigma"),
                func.avg(
                    Member.mu
                    - RatingCalculationConfig.TRUESKILL_CONSERVATIVE_K * Member.sigma
                ).label("avg_score"),
            )
            .filter(Member.leaved_date.is_(None))
            .first()
        )

        # 總比賽數
        total_matches = db.session.query(func.count(MatchRecord.id)).scalar() or 0

        # 平均比賽數
        total_players = total_members + total_guests
        avg_matches = total_matches / total_players if total_players > 0 else 0

        return {
            "total_players": total_players,
            "total_members": total_members,
            "total_guests": total_guests,
            "total_active_players": total_active,
            "total_matches": total_matches,
            "average_skill": {
                "mu": round(avg_stats.avg_mu or 25, 2),
                "sigma": round(avg_stats.avg_sigma or 8.33, 2),
                "conservative_score": round(avg_stats.avg_score or 0, 2),
            },
            "average_matches_per_player": round(avg_matches, 2),
        }

    @staticmethod
    def _get_score_distribution() -> Dict:
        """獲取分數分佈"""
        # 使用 Member 的 get_active_players 方法（如果存在）
        active_members_query = Member.query.filter(
            Member.leaved_date.is_(None),
            or_(
                Member.is_guest == True,
                and_(Member.is_guest == False, Member.user_id.isnot(None)),
            ),
        )

        active_members = active_members_query.all()

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
            "std_dev": round(LeaderboardService._calculate_std_dev(scores), 2),
        }

    @staticmethod
    def _calculate_std_dev(values: List[float]) -> float:
        """計算標準差"""
        if not values:
            return 0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance**0.5

    @staticmethod
    def _get_experience_distribution() -> Dict:
        """獲取經驗等級分佈"""
        # 由於 experience_level 是計算屬性，需要在 Python 中計算
        active_members = Member.query.filter(Member.leaved_date.is_(None)).all()

        distribution = {}
        for member in active_members:
            level = member.experience_level
            distribution[level] = distribution.get(level, 0) + 1

        return distribution

    @staticmethod
    def _get_organization_distribution() -> Dict:
        """獲取組織分佈"""
        distribution = (
            db.session.query(Organization.name, func.count(Member.id).label("count"))
            .join(Member, Organization.id == Member.organization_id)
            .filter(Member.leaved_date.is_(None))
            .group_by(Organization.name)
            .all()
        )

        return {org: count for org, count in distribution}

    @staticmethod
    def _get_activity_statistics() -> Dict:
        """獲取活躍度統計"""
        now = datetime.now()
        last_week = now - timedelta(days=7)
        last_month = now - timedelta(days=30)

        # 最近一週的比賽數
        matches_last_week = (
            db.session.query(func.count(MatchRecord.id))
            .join(Match, MatchRecord.match_id == Match.id)
            .filter(Match.match_date >= last_week)
            .scalar()
            or 0
        )

        # 最近一個月的比賽數
        matches_last_month = (
            db.session.query(func.count(MatchRecord.id))
            .join(Match, MatchRecord.match_id == Match.id)
            .filter(Match.match_date >= last_month)
            .scalar()
            or 0
        )

        # 最近一個月新加入球員
        new_last_month = Member.query.filter(Member.joined_date >= last_month).count()

        return {
            "matches_last_week": matches_last_week,
            "matches_last_month": matches_last_month,
            "new_players_last_month": new_last_month,
        }

    @staticmethod
    def _get_default_statistics() -> Dict:
        """獲取預設統計信息（錯誤時使用）"""
        return {
            "total_players": 0,
            "total_members": 0,
            "total_guests": 0,
            "total_active_players": 0,
            "total_matches": 0,
            "average_skill": {"mu": 25, "sigma": 8.33, "conservative_score": 0},
            "average_matches_per_player": 0,
            "score_distribution": {},
            "experience_distribution": {},
            "organization_distribution": {},
            "matches_last_week": 0,
            "matches_last_month": 0,
            "new_players_last_month": 0,
            "last_updated": None,
            "data_freshness": "無數據",
        }
