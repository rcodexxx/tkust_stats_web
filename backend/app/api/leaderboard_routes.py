# backend/app/api/member_routes.py
from flask import jsonify, current_app
from sqlalchemy import func

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
    回傳成員的姓名、組織、計算後的積分(score)等，並嚴格按照 score (mu - 3*sigma) 降序排列。
    """
    try:
        active_members_query = TeamMember.query.filter_by(is_active=True)
        potential_members = active_members_query.order_by(
            TeamMember.mu.desc(), TeamMember.sigma.asc()
        ).all()

        leaderboard_data = []
        for member in potential_members:
            member_id = member.id

            # 計算勝負場次 (與之前邏輯相同)
            wins = (
                db.session.query(func.count(MatchRecord.id))
                .filter(
                    (
                        (
                            (MatchRecord.side_a_player1_id == member_id)
                            | (MatchRecord.side_a_player2_id == member_id)
                        )
                        & (MatchRecord.side_a_outcome == OutcomeEnum.WIN)
                    ),
                    (
                        (
                            (MatchRecord.side_b_player1_id == member_id)
                            | (MatchRecord.side_b_player2_id == member_id)
                        )
                        & (MatchRecord.side_a_outcome == OutcomeEnum.LOSS)
                    ),
                )
                .scalar()
                or 0
            )

            losses = (
                db.session.query(func.count(MatchRecord.id))
                .filter(
                    (
                        (
                            (MatchRecord.side_a_player1_id == member_id)
                            | (MatchRecord.side_a_player2_id == member_id)
                        )
                        & (MatchRecord.side_a_outcome == OutcomeEnum.LOSS)
                    ),
                    (
                        (
                            (MatchRecord.side_b_player1_id == member_id)
                            | (MatchRecord.side_b_player2_id == member_id)
                        )
                        & (MatchRecord.side_a_outcome == OutcomeEnum.WIN)
                    ),
                )
                .scalar()
                or 0
            )

            total_matches = wins + losses

            if total_matches > 0:
                member_dict = member.to_dict()
                member_dict["wins"] = wins
                member_dict["losses"] = losses
                member_dict["total_matches"] = total_matches
                leaderboard_data.append(member_dict)

        leaderboard_data.sort(key=lambda m: m["score"], reverse=True)

        return jsonify(leaderboard_data)

    except Exception as e:
        current_app.logger.error(f"Error in get_leaderboard: {str(e)}", exc_info=True)
        return jsonify({"error": "獲取排行榜時發生錯誤。"}), 500
