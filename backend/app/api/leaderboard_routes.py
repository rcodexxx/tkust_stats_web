# backend/app/api/member_routes.py
from flask import jsonify
from . import bp # 假設從 app.api.__init__ 匯入
from ..models.team_member import TeamMember
from sqlalchemy.orm import joinedload # 用於預載入關聯數據

@bp.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    """獲取排行榜數據，按分數降序排列 (只包含活躍成員)"""
    try:
        members = TeamMember.query.order_by(TeamMember.name.desc()).all()
        leaderboard_data = []
        for member in members:
            leaderboard_data.append({
                "id": member.id,
                "name": member.name,
                "score": member.score,
                "student_id": member.student_id,
                "gender": member.gender.value if member.gender else None,
                "position": member.position.value if member.position else None,
                # 可以在排行榜中省略 join_date, leave_date, notes, is_active 等，除非前端需要
            })
        return jsonify(leaderboard_data)
    except Exception as e:
        print(f"Error in get_leaderboard: {e}")
        return jsonify({"error": "An error occurred while fetching the leaderboard."}), 500