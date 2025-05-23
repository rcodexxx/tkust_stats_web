from flask import request, jsonify, current_app  # <--- 加入 current_app (如果您想用 app.logger)
from . import bp
from ..extensions import db  # <--- 之前是 from ..extensions import db
from ..models.team_member import TeamMember
from ..models.match_record import MatchRecord
from ..models.enums import MatchTypeEnum, OutcomeEnum, MatchFormatEnum, GenderEnum
from ..services.rating_service import calculate_new_ratings_1v1, calculate_new_ratings_2v2
from sqlalchemy.exc import IntegrityError
from datetime import datetime


@bp.route('/matches/record', methods=['POST'])
def record_match():
    data = request.get_json()
    current_app.logger.debug(f"Received payload for /api/matches/record: {data}")

    if not data:
        current_app.logger.error("Request payload was not JSON or was empty.")
        return jsonify({"error": "Request payload must be JSON and Content-Type must be application/json"}), 400

    # --- 1. 提取數據 ---
    errors = {}

    match_date_str = data.get('match_date')
    match_type_str = data.get('match_type')
    match_format_str = data.get('match_format')

    # 先提取 ID 字串，後面再轉換和驗證
    side_a_p1_id_str = data.get('side_a_player1_id')
    side_a_p2_id_str = data.get('side_a_player2_id')

    side_b_p1_id_str = data.get('side_b_player1_id')
    side_b_p2_id_str = data.get('side_b_player2_id')

    # 您的 MatchRecord 模型使用的是 side_a_games_won 和 side_b_games_won
    # 但您在必填欄位檢查和payload提取時用了 side_a_score_str 和 side_b_score_str
    # 這裡統一為前端 payload 和模型一致的名稱
    side_a_games_won_val = data.get('side_a_games_won')  # 前端 payload 使用的是 games_won
    side_b_games_won_val = data.get('side_b_games_won')

    side_a_outcome_str = data.get('side_a_outcome')
    match_notes = data.get('match_notes', "")

    # --- 2. 必填欄位基礎檢查 (檢查 key 是否存在以及是否有非空值) ---
    required_fields_from_payload = {
        'match_date': match_date_str,
        'match_type': match_type_str,
        'match_format': match_format_str,
        'side_a_player1_id': side_a_p1_id_str,  # 用提取出來的變數
        'side_b_player1_id': side_b_p1_id_str,
        'side_a_games_won': side_a_games_won_val,  # 使用提取的 games_won
        'side_b_games_won': side_b_games_won_val,
        'side_a_outcome': side_a_outcome_str
    }

    for field, value in required_fields_from_payload.items():
        if value is None or (isinstance(value, str) and value.strip() == ""):
            errors[field] = f"{field} is required and cannot be empty."

    # 如果基礎必填欄位有錯，先返回
    if errors:
        current_app.logger.warning(f"Initial validation failed: {errors}")
        return jsonify({"message": "Input validation failed", "errors": errors}), 400

    # --- 3. 數據類型轉換與進一步驗證 ---
    match_date_obj = None
    try:
        match_date_obj = datetime.strptime(match_date_str, '%Y-%m-%d').date()
    except ValueError:
        errors['match_date'] = "Invalid match_date format. Expected YYYY-MM-DD."

    match_type_enum = MatchTypeEnum.get_by_name(match_type_str)
    if not match_type_enum:
        errors['match_type'] = f"Invalid match_type: '{match_type_str}'. Valid are: {[e.name for e in MatchTypeEnum]}."

    match_format_enum = MatchFormatEnum.get_by_name(match_format_str)
    if not match_format_enum:
        errors[
            'match_format'] = f"Invalid match_format: '{match_format_str}'. Valid are: {[e.name for e in MatchFormatEnum]}."

    side_a_outcome_enum = OutcomeEnum.get_by_name(side_a_outcome_str)
    if not side_a_outcome_enum or side_a_outcome_enum not in [OutcomeEnum.WIN, OutcomeEnum.LOSS]:
        errors['side_a_outcome'] = f"Outcome must be WIN or LOSS: '{side_a_outcome_str}'."

    # 轉換並獲取球員實例
    side_a_p1_id, side_a_p2_id, side_b_p1_id, side_b_p2_id = None, None, None, None
    side_a_p1, side_a_p2, side_b_p1, side_b_p2 = None, None, None, None

    try:
        side_a_p1_id = int(side_a_p1_id_str)
        side_b_p1_id = int(side_b_p1_id_str)
        if side_a_p2_id_str is not None: side_a_p2_id = int(side_a_p2_id_str)
        if side_b_p2_id_str is not None: side_b_p2_id = int(side_b_p2_id_str)
    except (ValueError, TypeError):
        errors['player_ids'] = "Player IDs must be valid integers."
        # 如果 player ID 不是數字，後面的 db.session.get 會出錯，所以這裡如果出錯應提前返回
        if errors:  # 再次檢查，因為上面可能已經有其他錯誤
            current_app.logger.warning(f"Player ID conversion failed or other errors: {errors}")
            return jsonify({"message": "Input validation failed", "errors": errors}), 400

    # 確保在嘗試 .id 之前，這些物件不是 None
    if side_a_p1_id:
        side_a_p1 = db.session.get(TeamMember, side_a_p1_id)
        if not side_a_p1: errors.setdefault('side_a_player1_id', []).append(
            f"Side A Player 1 (ID: {side_a_p1_id}) not found.")

    if side_b_p1_id:
        side_b_p1 = db.session.get(TeamMember, side_b_p1_id)
        if not side_b_p1: errors.setdefault('side_b_player1_id', []).append(
            f"Side B Player 1 (ID: {side_b_p1_id}) not found.")

    player_ids_in_match = set()  # 用於檢查球員唯一性
    if side_a_p1: player_ids_in_match.add(side_a_p1.id)
    if side_b_p1: player_ids_in_match.add(side_b_p1.id)

    if match_type_enum == MatchTypeEnum.DOUBLES:
        if not side_a_p2_id:
            errors.setdefault('side_a_player2_id', []).append("Side A Player 2 is required for doubles.")
        elif side_a_p1 and side_a_p1.id == side_a_p2_id:
            errors.setdefault('side_a_player2_id', []).append("Side A players must be different.")
        else:
            side_a_p2 = db.session.get(TeamMember, side_a_p2_id)
            if not side_a_p2:
                errors.setdefault('side_a_player2_id', []).append(f"Side A Player 2 (ID: {side_a_p2_id}) not found.")
            elif side_a_p2:
                player_ids_in_match.add(side_a_p2.id)

        if not side_b_p2_id:
            errors.setdefault('side_b_player2_id', []).append("Side B Player 2 is required for doubles.")
        elif side_b_p1 and side_b_p1.id == side_b_p2_id:
            errors.setdefault('side_b_player2_id', []).append("Side B players must be different.")
        else:
            side_b_p2 = db.session.get(TeamMember, side_b_p2_id)
            if not side_b_p2:
                errors.setdefault('side_b_player2_id', []).append(f"Side B Player 2 (ID: {side_b_p2_id}) not found.")
            elif side_b_p2:
                player_ids_in_match.add(side_b_p2.id)

    elif match_type_enum == MatchTypeEnum.SINGLES:
        if side_a_p2_id is not None: errors.setdefault('side_a_player2_id', []).append(
            "Singles match should not have Side A Player 2.")
        if side_b_p2_id is not None: errors.setdefault('side_b_player2_id', []).append(
            "Singles match should not have Side B Player 2.")
        side_a_p2_id, side_b_p2_id = None, None  # 確保它們是 None
        side_a_p2, side_b_p2 = None, None

    # 檢查球員是否跨隊 (在所有球員物件都已嘗試獲取後)
    if side_a_p1 and side_b_p1:  # 確保主要球員存在才進行比較
        side_a_ids_set = {p.id for p in [side_a_p1, side_a_p2] if p}
        side_b_ids_set = {p.id for p in [side_b_p1, side_b_p2] if p}
        if side_a_ids_set.intersection(side_b_ids_set):
            errors.setdefault('players', []).append("A player cannot be on both competing sides.")

    # 檢查球員總數是否正確 (在所有球員物件都已嘗試獲取後)
    # player_ids_in_match 此時包含了所有成功找到的、不重複的球員ID
    expected_player_count = 0
    if match_type_enum == MatchTypeEnum.SINGLES:
        expected_player_count = 2
    elif match_type_enum == MatchTypeEnum.DOUBLES:
        expected_player_count = 4

    # 計算實際參與的有效球員數量
    actual_valid_players = sum(1 for p in [side_a_p1, side_a_p2, side_b_p1, side_b_p2] if p)

    if match_type_enum and len(player_ids_in_match) != expected_player_count:
        # 只有當所有必需的球員ID都提供了，但找到的球員數量不對時，這個錯誤才有意義
        # 如果是因為某個球員ID找不到而導致數量不對，前面的錯誤已經捕獲了
        if not errors.get('players') and actual_valid_players == expected_player_count:  # 避免因找不到球員而重複報錯
            errors.setdefault('players', []).append(
                f"Incorrect number of unique players for {match_type_str} match. Expected {expected_player_count}, got {len(player_ids_in_match)} (unique and found)."
            )

    # 轉換比分
    side_a_games_won, side_b_games_won = None, None
    try:
        if side_a_games_won_val is not None: side_a_games_won = int(side_a_games_won_val)
        if side_b_games_won_val is not None: side_b_games_won = int(side_b_games_won_val)
        if (side_a_games_won is not None and side_a_games_won < 0) or \
                (side_b_games_won is not None and side_b_games_won < 0):
            errors['scores'] = "Games won cannot be negative."
    except (ValueError, TypeError):
        errors['scores'] = "Games won must be integers."

    if errors:  # 最終檢查所有累積的錯誤
        current_app.logger.warning(f"Validation failed for /api/matches/record. Errors: {errors}")
        return jsonify({"message": "Input validation failed", "errors": errors}), 400

    # --- 4. 創建 MatchRecord 實例並更新分數 ---
    try:
        new_match = MatchRecord(
            match_date=match_date_obj,
            match_type=match_type_enum,
            match_format=match_format_enum,
            side_a_player1_id=side_a_p1.id,  # 此時 side_a_p1 等物件已確認存在
            side_a_player2_id=side_a_p2.id if side_a_p2 else None,
            side_b_player1_id=side_b_p1.id,
            side_b_player2_id=side_b_p2.id if side_b_p2 else None,
            side_a_games_won=side_a_games_won,  # 使用已轉換為 int 的值
            side_b_games_won=side_b_games_won,  # 使用已轉換為 int 的值
            side_a_outcome=side_a_outcome_enum,
            match_notes=match_notes
        )
        db.session.add(new_match)

        # 更新 TrueSkill 評分
        if match_type_enum == MatchTypeEnum.SINGLES:
            ((new_a1_mu, new_a1_sigma), (new_b1_mu, new_b1_sigma)) = calculate_new_ratings_1v1(
                side_a_p1.mu, side_a_p1.sigma, side_a_p1.gender,
                side_b_p1.mu, side_b_p1.sigma, side_b_p1.gender,
                side_a_outcome_enum == OutcomeEnum.WIN
            )
            side_a_p1.mu, side_a_p1.sigma = new_a1_mu, new_a1_sigma
            side_b_p1.mu, side_b_p1.sigma = new_b1_mu, new_b1_sigma

        elif match_type_enum == MatchTypeEnum.DOUBLES:
            # 確保所有雙打球員都已成功獲取
            if not (side_a_p1 and side_a_p2 and side_b_p1 and side_b_p2):
                # 這個情況理論上應該在前面的驗證中被攔截，但作為最後防線
                current_app.logger.error("Attempted to calculate doubles rating with missing player objects.")
                return jsonify({"message": "Internal error: Missing player data for doubles rating."}), 500

            ((t1p1_mu, t1p1_sigma), (t1p2_mu, t1p2_sigma),
             (t2p1_mu, t2p1_sigma), (t2p2_mu, t2p2_sigma)) = calculate_new_ratings_2v2(
                side_a_p1.mu, side_a_p1.sigma, side_a_p1.gender,
                side_a_p2.mu, side_a_p2.sigma, side_a_p2.gender,
                side_b_p1.mu, side_b_p1.sigma, side_b_p1.gender,
                side_b_p2.mu, side_b_p2.sigma, side_b_p2.gender,
                side_a_outcome_enum == OutcomeEnum.WIN
            )
            side_a_p1.mu, side_a_p1.sigma = t1p1_mu, t1p1_sigma
            side_a_p2.mu, side_a_p2.sigma = t1p2_mu, t1p2_sigma
            side_b_p1.mu, side_b_p1.sigma = t2p1_mu, t2p1_sigma
            side_b_p2.mu, side_b_p2.sigma = t2p2_mu, t2p2_sigma

        db.session.commit()

        updated_player_ratings = {}
        for p in [side_a_p1, side_a_p2, side_b_p1, side_b_p2]:
            if p:
                updated_player_ratings[p.id] = {"name": p.name, "new_score": p.score, "new_mu": round(p.mu, 2),
                                                "new_sigma": round(p.sigma, 2)}

        return jsonify({
            "message": "Match recorded successfully and TrueSkill ratings updated!",
            "match": new_match.to_dict(),
            "updated_player_ratings": updated_player_ratings
        }), 201

    except IntegrityError as e:
        db.session.rollback()
        current_app.logger.error(f"IntegrityError recording match: {str(e.orig)}", exc_info=True)
        return jsonify({"message": "Database integrity error.", "error_code": "DB_INTEGRITY"}), 409
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Unexpected error recording match: {str(e)}", exc_info=True)
        return jsonify({"message": "An unexpected server error occurred.", "error_code": "SERVER_ERROR"}), 500