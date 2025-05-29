# backend/app/api/member_routes.py
from flask import jsonify, current_app
from sqlalchemy import or_, func

from . import bp
from ..extensions import db
from ..models.enums import OutcomeEnum
from ..models.match_record import MatchRecord
from ..models.member import TeamMember


@bp.route("/leaderboard", methods=["GET"])
def get_leaderboard():
    """
    獲取排行榜數據。
    只包含至少參與過一場有效比賽的活躍成員。
    回傳成員的姓名、組織、計算後的積分(score)等。
    排序邏輯：先按 TrueSkill 的 mu 降序、sigma 升序從資料庫獲取，
              然後在 Python 中按最終的 'score' 屬性進行排序。
    """
    try:
        # 1. 獲取所有活躍的球隊成員，並進行初步的 TrueSkill 排序
        active_members = (
            TeamMember.query.filter_by(is_active=True)
            .order_by(TeamMember.mu.desc(), TeamMember.sigma.asc())
            .all()
        )

        if not active_members:
            current_app.logger.info("No active members found for leaderboard.")
            return jsonify([])  # 如果沒有活躍成員，直接回傳空列表

        leaderboard_data = []
        for member in active_members:
            member_id = member.id

            # 2. 為每個成員計算有效比賽的勝場數
            wins = (
                db.session.query(func.count(MatchRecord.id))
                .filter(
                    or_(  # 球員獲勝的兩種情況
                        (  # 情況 A: 球員在 A 方且 A 方勝
                            (
                                (MatchRecord.side_a_player1_id == member_id)
                                | (MatchRecord.side_a_player2_id == member_id)
                            )
                            & (MatchRecord.side_a_outcome == OutcomeEnum.WIN)
                        ),
                        (  # 情況 B: 球員在 B 方且 B 方勝 (即 A 方敗)
                            (
                                (MatchRecord.side_b_player1_id == member_id)
                                | (MatchRecord.side_b_player2_id == member_id)
                            )
                            & (MatchRecord.side_a_outcome == OutcomeEnum.LOSS)
                        ),
                    ),
                )
                .scalar()
                or 0
            )

            # 3. 為每個成員計算有效比賽的敗場數
            losses = (
                db.session.query(func.count(MatchRecord.id))
                .filter(
                    or_(  # 球員失敗的兩種情況
                        (  # 情況 A: 球員在 A 方且 A 方敗
                            (
                                (MatchRecord.side_a_player1_id == member_id)
                                | (MatchRecord.side_a_player2_id == member_id)
                            )
                            & (MatchRecord.side_a_outcome == OutcomeEnum.LOSS)
                        ),
                        (  # 情況 B: 球員在 B 方且 B 方敗 (即 A 方勝)
                            (
                                (MatchRecord.side_b_player1_id == member_id)
                                | (MatchRecord.side_b_player2_id == member_id)
                            )
                            & (MatchRecord.side_a_outcome == OutcomeEnum.WIN)
                        ),
                    ),
                )
                .scalar()
                or 0
            )

            total_matches = wins + losses

            # 4. 只有當總參與比賽場次 > 0 時才加入到排行榜
            win_rate = (wins / total_matches) * 100 if total_matches > 0 else 0
            if total_matches > 0:
                member_dict = member.to_dict()
                member_dict["wins"] = wins
                member_dict["losses"] = losses
                member_dict["total_matches"] = total_matches
                member_dict["win_rate"] = win_rate
                leaderboard_data.append(member_dict)
            else:
                current_app.logger.debug(
                    f"Member {member.name} (ID: {member.id}) has 0 total matches, excluded from leaderboard."
                )

        # 5. 在 Python 中根據模型計算的 score 屬性進行最終排序
        leaderboard_data.sort(key=lambda m: m["score"], reverse=True)

        current_app.logger.info(
            f"Leaderboard generated with {len(leaderboard_data)} members."
        )
        return jsonify(leaderboard_data)

    except Exception as e:
        current_app.logger.error(f"Error in get_leaderboard: {str(e)}", exc_info=True)
        return jsonify({"error": "獲取排行榜時發生錯誤。"}), 500
