# backend/app/api/member_routes.py
from flask import jsonify
from . import bp # 假設從 app.api.__init__ 匯入
from ..models.team_member import TeamMember
from sqlalchemy.orm import joinedload # 用於預載入關聯數據

@bp.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    """獲取排行榜數據，按分數降序排列"""
    # 預載入 organization 和 racket_info 以避免 N+1 查詢
    members = TeamMember.query.options(
        joinedload(TeamMember.organization),
        joinedload(TeamMember.racket_info)
    ).order_by(TeamMember.score.desc()).all()

    leaderboard_data = []
    for member in members:
        leaderboard_data.append({
            "id": member.id,
            "name": member.name,
            "score": member.score,
            "student_id": member.student_id,
            "organization_name": member.organization.name if member.organization else None,
            "racket_display": f"{member.racket_info.brand} {member.racket_info.model_name}" if member.racket_info else None,
            "gender": member.gender.value if member.gender else None,
            "position": member.position.value if member.position else None, # 假設模型中是 position
        })
    return jsonify(leaderboard_data)