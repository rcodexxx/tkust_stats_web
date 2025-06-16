# your_project/app/services/rating_service.py
import trueskill
from flask import current_app

from ..extensions import db
from ..models import Match, MatchRecord, Member
from ..models.enums import GenderEnum, MatchOutcomeEnum

# --- 評分相關常數 ---
GENDER_BONUS_MU = 0.6

# --- 設定 TrueSkill 環境 ---
trueskill_env = trueskill.TrueSkill(draw_probability=0)


class RatingService:
    @staticmethod
    def _get_player_data(player_ids: list[int]) -> dict:
        """根據球員 ID 列表，一次性獲取他們的 Member 物件。"""
        if not player_ids:
            return {}
        players = Member.query.filter(Member.id.in_(player_ids)).all()
        return {p.id: p for p in players}

    @staticmethod
    def update_ratings_from_match(match_record: MatchRecord):
        """
        根據一場新的比賽結果，更新所有參與者的 TrueSkill 評分
        新增：根據比賽分差動態調整 Beta 參數
        """
        side_a_ids = [p_id for p_id in [match_record.player1_id, match_record.player2_id] if p_id]
        side_b_ids = [p_id for p_id in [match_record.player3_id, match_record.player4_id] if p_id]

        all_player_ids = side_a_ids + side_b_ids
        players_data = RatingService._get_player_data(all_player_ids)

        if len(players_data) != len(set(all_player_ids)):
            missing_ids = set(all_player_ids) - set(players_data.keys())
            current_app.logger.warning(f"評分中止：找不到球員 ID {missing_ids}。")
            return

        # 計算懸殊度 (D)
        total_games = match_record.a_games + match_record.b_games
        suspense_degree = abs(match_record.a_games - match_record.b_games) / total_games if total_games > 0 else 0

        # 動態調整 Beta 參數
        alpha = 0.5  # 調整係數，可設為配置參數
        default_beta = trueskill_env.beta
        dynamic_beta = default_beta * (1 - suspense_degree * alpha)

        # 創建臨時的 TrueSkill 環境，使用動態 Beta
        temp_env = trueskill.TrueSkill(
            mu=trueskill_env.mu,
            sigma=trueskill_env.sigma,
            beta=dynamic_beta,
            tau=trueskill_env.tau,
            draw_probability=trueskill_env.draw_probability
        )

        # 建立隊伍評分
        team1_ratings = {
            p_id: temp_env.create_rating(mu=players_data[p_id].mu, sigma=players_data[p_id].sigma)
            for p_id in side_a_ids
        }
        team2_ratings = {
            p_id: temp_env.create_rating(mu=players_data[p_id].mu, sigma=players_data[p_id].sigma)
            for p_id in side_b_ids
        }

        if match_record.side_a_outcome == MatchOutcomeEnum.WIN:
            ranks = [0, 1]
            winning_team_ids, losing_team_ids = side_a_ids, side_b_ids
        else:
            ranks = [1, 0]
            winning_team_ids, losing_team_ids = side_b_ids, side_a_ids

        # 使用動態 Beta 進行評分更新
        new_team1_ratings, new_team2_ratings = temp_env.rate([team1_ratings, team2_ratings], ranks=ranks)

        final_ratings = {}
        for p_id, rating in {**new_team1_ratings, **new_team2_ratings}.items():
            final_ratings[p_id] = {"mu": rating.mu, "sigma": rating.sigma}

        # 應用性別差異獎勵（保持原有邏輯）
        winning_team_genders = {p_id: players_data[p_id].gender for p_id in winning_team_ids}
        losing_team_genders = {p_id: players_data[p_id].gender for p_id in losing_team_ids}

        winner_has_female = GenderEnum.FEMALE in winning_team_genders.values()
        loser_has_male = GenderEnum.MALE in losing_team_genders.values()

        if winner_has_female and loser_has_male:
            for p_id, gender in winning_team_genders.items():
                if gender == GenderEnum.FEMALE:
                    final_ratings[p_id]["mu"] += GENDER_BONUS_MU
                    current_app.logger.info(f"性別獎勵已應用於球員 ID {p_id} (女性勝男性)。Mu +{GENDER_BONUS_MU}")

        # 將最終的評分寫回資料庫
        for p_id, new_rating_values in final_ratings.items():
            member = players_data.get(p_id)
            if member:
                member.mu = new_rating_values["mu"]
                member.sigma = new_rating_values["sigma"]

        current_app.logger.info(
            f"已為比賽記錄 ID {match_record.id} 更新評分。"
            f"懸殊度: {suspense_degree:.3f}, 動態Beta: {dynamic_beta:.3f}"
        )

    @staticmethod
    def recalculate_ratings_for_players(player_ids: list[int]):
        """
        為一組指定的球員，基於他們所有的比賽記錄，從頭重新計算評分。
        """
        if not player_ids:
            return

        current_app.logger.info(f"正在為球員 ID {player_ids} 重新計算評分...")

        # 1. 一次性獲取所有相關的 Member 物件
        players_to_recalculate = RatingService._get_player_data(player_ids)

        # 2. 在 Python 中將他們的評分重設為初始值
        current_ratings = {}
        for p_id, member in players_to_recalculate.items():
            member.mu = trueskill_env.mu
            member.sigma = trueskill_env.sigma
            current_ratings[p_id] = trueskill_env.create_rating(mu=member.mu, sigma=member.sigma)

        # 3. 獲取所有與這些球員相關的比賽記錄，並按時間順序排序
        relevant_matches = (
            MatchRecord.query.join(MatchRecord.match)
            .filter(
                db.or_(
                    MatchRecord.player1_id.in_(player_ids),
                    MatchRecord.player2_id.in_(player_ids),
                    MatchRecord.player3_id.in_(player_ids),
                    MatchRecord.player4_id.in_(player_ids),
                )
            )
            .order_by(Match.match_date.asc(), MatchRecord.id.asc())
            .all()
        )

        # 4. 按時間順序，逐場在記憶體中重新演算評分
        for match in relevant_matches:
            side_a_ids = [p_id for p_id in [match.player1_id, match.player2_id] if p_id]
            side_b_ids = [p_id for p_id in [match.player3_id, match.player4_id] if p_id]

            team1_current_ratings = {p_id: current_ratings[p_id] for p_id in side_a_ids if p_id in current_ratings}
            team2_current_ratings = {p_id: current_ratings[p_id] for p_id in side_b_ids if p_id in current_ratings}

            if not team1_current_ratings or not team2_current_ratings:
                continue

            ranks = [0, 1] if match.side_a_outcome == MatchOutcomeEnum.WIN else [1, 0]
            new_team1_ratings, new_team2_ratings = trueskill_env.rate(
                [team1_current_ratings, team2_current_ratings], ranks=ranks
            )

            # 更新 current_ratings 字典
            for p_id, rating in {**new_team1_ratings, **new_team2_ratings}.items():
                current_ratings[p_id] = rating

        # 5. 在所有計算完成後，將最終的評分更新回 Member 物件
        for p_id, final_rating in current_ratings.items():
            member = players_to_recalculate.get(p_id)
            if member:
                member.mu = final_rating.mu
                member.sigma = final_rating.sigma
