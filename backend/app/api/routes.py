# from flask import jsonify, request
# from . import bp
# from ..extensions import db
# from ..models.TeamMember import TeamMember
# from ..models.MatchRecord import MatchRecord
# from ..models.enums import MatchTypeEnum, OutcomeEnum # 確保 Enums 可用
# from datetime import datetime
#
# @bp.route('/leaderboard', methods=['GET'])
# def get_leaderboard():
#     members = TeamMember.query.filter_by(is_active=True).order_by(TeamMember.score.desc()).all()
#     leaderboard_data = [
#         {
#             "id": member.id,
#             "name": member.name,
#             "score": member.score,
#             "preferred_position": member.preferred_position.value if member.preferred_position else None
#         } for member in members
#     ]
#     return jsonify(leaderboard_data)
#
# @bp.route('/members', methods=['GET'])
# def get_members():
#     """獲取所有活躍球員列表，用於表單選擇"""
#     members = TeamMember.query.filter_by(is_active=True).order_by(TeamMember.name).all()
#     member_data = [{"id": member.id, "name": member.name} for member in members]
#     return jsonify(member_data)
#
# @bp.route('/matches/record', methods=['POST'])
# def record_match_api():
#     data = request.get_json()
#     if not data:
#         return jsonify({"error": "Request must be JSON"}), 400
#
#     # 從 data 中獲取比賽資訊
#     match_date_str = data.get('match_date')
#     player1_id = data.get('player1_id')
#     player2_id_str = data.get('player2_id')
#     match_type_str = data.get('match_type')
#     opponent_player1_name = data.get('opponent_player1_name')
#     our_score_str = data.get('our_score_str')
#     opponent_score_str = data.get('opponent_score_str')
#     outcome_str = data.get('outcome')
#
#     # 基本驗證 (在實際應用中應該更完善)
#     required_fields = [match_date_str, player1_id, match_type_str, outcome_str, opponent_player1_name, our_score_str, opponent_score_str]
#     if not all(required_fields):
#         return jsonify({"error": "Missing required fields"}), 400
#
#     try:
#         match_date = datetime.strptime(match_date_str, '%Y-%m-%d').date()
#         match_type = MatchTypeEnum[match_type_str.upper()]
#         outcome = OutcomeEnum[outcome_str.upper()]
#         player2_id = int(player2_id_str) if player2_id_str and str(player2_id_str).isdigit() else None
#
#         player1 = TeamMember.query.get(player1_id)
#         if not player1:
#             return jsonify({"error": f"Player 1 with id {player1_id} not found"}), 404
#
#         player2 = None
#         if match_type == MatchTypeEnum.DOUBLES:
#             if not player2_id:
#                 return jsonify({"error": "Player 2 is required for doubles match"}), 400
#             if player1_id == player2_id:
#                 return jsonify({"error": "Player 1 and Player 2 cannot be the same"}), 400
#             player2 = TeamMember.query.get(player2_id)
#             if not player2:
#                  return jsonify({"error": f"Player 2 with id {player2_id} not found"}), 404
#         elif player2_id: # 單打卻選了 player2
#             player2_id = None
#
#
#         new_match = MatchRecord(
#             match_date=match_date,
#             player1_id=player1_id,
#             player2_id=player2_id,
#             match_type=match_type,
#             opponent_player1_name=opponent_player1_name,
#             our_score_str=our_score_str,
#             opponent_score_str=opponent_score_str,
#             outcome=outcome
#         )
#         db.session.add(new_match)
#
#         # 更新球員分數
#         points_for_win = 3
#         points_for_loss = 1
#
#         if outcome == OutcomeEnum.WIN:
#             player1.score = (player1.score or 0) + points_for_win
#             if player2:
#                 player2.score = (player2.score or 0) + points_for_win
#         elif outcome == OutcomeEnum.LOSS:
#             player1.score = (player1.score or 0) + points_for_loss
#             if player2:
#                 player2.score = (player2.score or 0) + points_for_loss
#
#         db.session.commit()
#         return jsonify({"message": "Match recorded successfully", "match_id": new_match.id}), 201
#
#     except (KeyError, ValueError) as e: # 處理 Enum 轉換錯誤等
#          db.session.rollback()
#          return jsonify({"error": f"Invalid input data: {str(e)}"}), 400
#     except Exception as e:
#         db.session.rollback()
#         # Log the exception e
#         print(f"Error in record_match_api: {e}")
#         return jsonify({"error": "An internal server error occurred"}), 500