# your_project/app/services/rating_service.py
import trueskill
from flask import current_app

from ..extensions import db
from ..models import Member, MatchRecord
from ..models.enums import GenderEnum, MatchOutcomeEnum  # 確保導入 OutcomeEnum

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
        根據一場新的比賽結果，更新所有參與者的 TrueSkill 評分，並應用性別差異獎勵。
        """
        side_a_ids = [p_id for p_id in [match_record.player1_id, match_record.player2_id] if p_id]
        side_b_ids = [p_id for p_id in [match_record.player3_id, match_record.player4_id] if p_id]

        all_player_ids = side_a_ids + side_b_ids
        players_data = RatingService._get_player_data(all_player_ids)

        if len(players_data) != len(set(all_player_ids)):
            missing_ids = set(all_player_ids) - set(players_data.keys())
            current_app.logger.warning(f"評分中止：找不到球員 ID {missing_ids}。")
            return

        team1_ratings = {
            p_id: trueskill_env.create_rating(mu=players_data[p_id].mu, sigma=players_data[p_id].sigma)
            for p_id in side_a_ids
        }
        team2_ratings = {
            p_id: trueskill_env.create_rating(mu=players_data[p_id].mu, sigma=players_data[p_id].sigma)
            for p_id in side_b_ids
        }

        if match_record.side_a_outcome == MatchOutcomeEnum.WIN:
            ranks = [0, 1]
            winning_team_ids, losing_team_ids = side_a_ids, side_b_ids
        else:
            ranks = [1, 0]
            winning_team_ids, losing_team_ids = side_b_ids, side_a_ids

        # 1. 標準 TrueSkill 評分更新
        new_team1_ratings, new_team2_ratings = trueskill_env.rate([team1_ratings, team2_ratings], ranks=ranks)

        final_ratings = {}
        for p_id, rating in {**new_team1_ratings, **new_team2_ratings}.items():
            final_ratings[p_id] = {"mu": rating.mu, "sigma": rating.sigma}

        # 2. 應用性別差異獎勵
        winning_team_genders = {p_id: players_data[p_id].gender for p_id in winning_team_ids}
        losing_team_genders = {p_id: players_data[p_id].gender for p_id in losing_team_ids}

        winner_has_female = GenderEnum.FEMALE in winning_team_genders.values()
        loser_has_male = GenderEnum.MALE in losing_team_genders.values()

        if winner_has_female and loser_has_male:
            for p_id, gender in winning_team_genders.items():
                if gender == GenderEnum.FEMALE:
                    final_ratings[p_id]["mu"] += GENDER_BONUS_MU
                    current_app.logger.info(f"性別獎勵已應用於球員 ID {p_id} (女性勝男性)。Mu +{GENDER_BONUS_MU}")

        # 3. 將最終的評分寫回資料庫的 Member 物件
        for p_id, new_rating_values in final_ratings.items():
            member = players_data.get(p_id)
            if member:
                member.mu = new_rating_values["mu"]
                member.sigma = new_rating_values["sigma"]

        current_app.logger.info(f"已為比賽記錄 ID {match_record.id} 更新評分。")

    @staticmethod
    def recalculate_ratings_for_players(player_ids: list[int]):
        """
        為一組指定的球員，基於他們所有的比賽記錄，從頭重新計算評分。
        """
        if not player_ids:
            return

        current_app.logger.info(f"正在為球員 ID {player_ids} 重新計算評分...")

        Member.query.filter(Member.id.in_(player_ids)).update(
            {"mu": trueskill_env.mu, "sigma": trueskill_env.sigma}, synchronize_session="fetch"
        )

        relevant_matches = (
            MatchRecord.query.filter(
                db.or_(
                    MatchRecord.player1_id.in_(player_ids),
                    MatchRecord.player2_id.in_(player_ids),
                    MatchRecord.player3_id.in_(player_ids),
                    MatchRecord.player4_id.in_(player_ids),
                )
            )
            .order_by(MatchRecord.match_date.asc(), MatchRecord.id.asc())
            .all()
        )

        for match in relevant_matches:
            RatingService.update_ratings_from_match(match)

        current_app.logger.info(f"為球員 ID {player_ids} 的評分重新計算完成。")
