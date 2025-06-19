import trueskill

from ..extensions import db
from ..models import Match, MatchRecord, Member
from ..models.enums import GenderEnum, MatchOutcomeEnum

# 性別獎勵/懲罰參數
GENDER_BONUS_MU = 0.6  # 女生贏男生時的額外加分
MALE_WIN_PENALTY = 0.3  # 男生贏有女生隊伍時的加分減少比例
MALE_LOSE_PENALTY = 0.4  # 男生輸給有女生隊伍時的額外扣分
FEMALE_LOSE_MITIGATION = 0.5  # 女生輸給男生時的扣分減輕比例
MALE_WITH_FEMALE_LOSE_MITIGATION = 0.3  # 男生有女隊友輸球時的扣分減輕比例
MALE_WITH_FEMALE_LOSE_MITIGATION = (
    0.3  # 男生有女隊友輸球時的扣分減輕比例時的加分減少比例
)
MALE_LOSE_PENALTY = 0.4  # 男生輸給有女生隊伍時的額外扣分
FEMALE_LOSE_MITIGATION = 0.5  # 女生輸給男生時的扣分減輕比例

trueskill_env = trueskill.TrueSkill(draw_probability=0)


class RatingService:
    @staticmethod
    def _get_player_data(player_ids: list[int]) -> dict:
        """批次獲取球員資料，回傳以 ID 為鍵的字典"""
        if not player_ids:
            return {}
        players = Member.query.filter(Member.id.in_(player_ids)).all()
        return {p.id: p for p in players}

    @staticmethod
    def _calculate_dynamic_beta(a_games: int, b_games: int) -> float:
        """
        根據比賽分差計算動態 Beta 值
        分差越大 → Beta 越小 → 評分變化越大
        """
        total_games = a_games + b_games
        if total_games == 0:
            return trueskill_env.beta

        suspense_degree = abs(a_games - b_games) / total_games
        return trueskill_env.beta * (1 - suspense_degree * 0.5)

    @staticmethod
    def _apply_gender_adjustments(
        final_ratings: dict,
        winning_team: list[int],
        losing_team: list[int],
        players: dict,
        base_ratings: dict,
    ):
        """
        應用性別獎勵/懲罰機制
        只要場上有女生就會觸發調整
        """
        winning_genders = {p_id: players[p_id].gender for p_id in winning_team}
        losing_genders = {p_id: players[p_id].gender for p_id in losing_team}

        winner_has_female = GenderEnum.FEMALE in winning_genders.values()
        winner_has_male = GenderEnum.MALE in winning_genders.values()
        loser_has_female = GenderEnum.FEMALE in losing_genders.values()
        loser_has_male = GenderEnum.MALE in losing_genders.values()

        # 場上無女生則不調整
        if not (winner_has_female or loser_has_female):
            return

        # 情況1: 女生贏男生 - 女生額外加分
        if winner_has_female and loser_has_male:
            for p_id, gender in winning_genders.items():
                if gender == GenderEnum.FEMALE:
                    final_ratings[p_id]["mu"] += GENDER_BONUS_MU

        # 情況2: 男生贏有女生的隊伍 - 男生加分減少
        if winner_has_male and loser_has_female:
            for p_id, gender in winning_genders.items():
                if gender == GenderEnum.MALE:
                    mu_change = final_ratings[p_id]["mu"] - base_ratings[p_id]["mu"]
                    if mu_change > 0:
                        final_ratings[p_id]["mu"] -= mu_change * MALE_WIN_PENALTY

        # 情況3: 男生輸給有女生的隊伍 - 男生額外扣分
        if loser_has_male and winner_has_female:
            for p_id, gender in losing_genders.items():
                if gender == GenderEnum.MALE:
                    final_ratings[p_id]["mu"] -= MALE_LOSE_PENALTY

        # 情況4: 女生輸給男生 - 女生扣分減輕
        if loser_has_female and winner_has_male:
            for p_id, gender in losing_genders.items():
                if gender == GenderEnum.FEMALE:
                    mu_change = final_ratings[p_id]["mu"] - base_ratings[p_id]["mu"]
                    if mu_change < 0:
                        final_ratings[p_id]["mu"] += (
                            abs(mu_change) * FEMALE_LOSE_MITIGATION
                        )

        # 情況5: 男生有女隊友輸球 - 男生扣分減輕
        if loser_has_female and loser_has_male:
            for p_id, gender in losing_genders.items():
                if gender == GenderEnum.MALE:
                    mu_change = final_ratings[p_id]["mu"] - base_ratings[p_id]["mu"]
                    if mu_change < 0:
                        final_ratings[p_id]["mu"] += (
                            abs(mu_change) * MALE_WITH_FEMALE_LOSE_MITIGATION
                        )

    @staticmethod
    def update_ratings_from_match(match_record: MatchRecord):
        """
        根據單場比賽結果更新所有參與者的評分
        包含：動態 Beta、性別調整、TrueSkill 實力差異
        """
        side_a_ids = [
            p_id for p_id in [match_record.player1_id, match_record.player2_id] if p_id
        ]
        side_b_ids = [
            p_id for p_id in [match_record.player3_id, match_record.player4_id] if p_id
        ]

        all_player_ids = side_a_ids + side_b_ids
        players_data = RatingService._get_player_data(all_player_ids)

        # 確認所有球員資料都存在
        if len(players_data) != len(set(all_player_ids)):
            return

        # 計算動態 Beta
        dynamic_beta = RatingService._calculate_dynamic_beta(
            match_record.a_games, match_record.b_games
        )

        # 建立動態 TrueSkill 環境
        temp_env = trueskill.TrueSkill(
            mu=trueskill_env.mu,
            sigma=trueskill_env.sigma,
            beta=dynamic_beta,
            tau=trueskill_env.tau,
            draw_probability=trueskill_env.draw_probability,
        )

        # 建立兩隊的當前評分
        team1_ratings = {
            p_id: temp_env.create_rating(
                mu=players_data[p_id].mu, sigma=players_data[p_id].sigma
            )
            for p_id in side_a_ids
        }
        team2_ratings = {
            p_id: temp_env.create_rating(
                mu=players_data[p_id].mu, sigma=players_data[p_id].sigma
            )
            for p_id in side_b_ids
        }

        # 保存原始評分用於性別調整計算
        base_ratings = {
            p_id: {"mu": players_data[p_id].mu, "sigma": players_data[p_id].sigma}
            for p_id in all_player_ids
        }

        # 決定勝負隊伍
        if match_record.side_a_outcome == MatchOutcomeEnum.WIN:
            ranks = [0, 1]  # A隊勝
            winning_team_ids, losing_team_ids = side_a_ids, side_b_ids
        else:
            ranks = [1, 0]  # B隊勝
            winning_team_ids, losing_team_ids = side_b_ids, side_a_ids

        # TrueSkill 評分更新
        new_team1_ratings, new_team2_ratings = temp_env.rate(
            [team1_ratings, team2_ratings], ranks=ranks
        )

        # 合併評分結果
        final_ratings = {}
        for p_id, rating in {**new_team1_ratings, **new_team2_ratings}.items():
            final_ratings[p_id] = {"mu": rating.mu, "sigma": rating.sigma}

        # 應用性別調整
        RatingService._apply_gender_adjustments(
            final_ratings, winning_team_ids, losing_team_ids, players_data, base_ratings
        )

        # 更新資料庫
        for p_id, new_rating in final_ratings.items():
            member = players_data.get(p_id)
            if member:
                member.mu = new_rating["mu"]
                member.sigma = new_rating["sigma"]

    @staticmethod
    def recalculate_ratings_for_players(player_ids: list[int]):
        """
        為指定球員重新計算所有歷史比賽的評分
        從初始評分開始，按時間順序重新演算
        """
        if not player_ids:
            return

        players_to_recalculate = RatingService._get_player_data(player_ids)

        # 重設為初始評分
        current_ratings = {}
        for p_id, member in players_to_recalculate.items():
            member.mu = trueskill_env.mu
            member.sigma = trueskill_env.sigma
            current_ratings[p_id] = trueskill_env.create_rating(
                mu=member.mu, sigma=member.sigma
            )

        # 獲取所有相關比賽，按時間排序
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

        # 逐場重新計算
        for match in relevant_matches:
            side_a_ids = [p_id for p_id in [match.player1_id, match.player2_id] if p_id]
            side_b_ids = [p_id for p_id in [match.player3_id, match.player4_id] if p_id]

            all_match_player_ids = side_a_ids + side_b_ids
            all_match_players_data = RatingService._get_player_data(
                all_match_player_ids
            )

            # 計算動態 Beta
            dynamic_beta = RatingService._calculate_dynamic_beta(
                match.a_games, match.b_games
            )

            # 建立動態環境
            temp_env = trueskill.TrueSkill(
                mu=trueskill_env.mu,
                sigma=trueskill_env.sigma,
                beta=dynamic_beta,
                tau=trueskill_env.tau,
                draw_probability=trueskill_env.draw_probability,
            )

            # 使用當前計算狀態的評分
            team1_current_ratings = {}
            team2_current_ratings = {}

            for p_id in side_a_ids:
                if p_id in current_ratings:
                    team1_current_ratings[p_id] = temp_env.create_rating(
                        mu=current_ratings[p_id].mu, sigma=current_ratings[p_id].sigma
                    )

            for p_id in side_b_ids:
                if p_id in current_ratings:
                    team2_current_ratings[p_id] = temp_env.create_rating(
                        mu=current_ratings[p_id].mu, sigma=current_ratings[p_id].sigma
                    )

            if not team1_current_ratings or not team2_current_ratings:
                continue

            # 保存評分更新前的狀態
            base_ratings = {}
            for p_id in all_match_player_ids:
                if p_id in current_ratings:
                    base_ratings[p_id] = {
                        "mu": current_ratings[p_id].mu,
                        "sigma": current_ratings[p_id].sigma,
                    }

            # 決定勝負
            if match.side_a_outcome == MatchOutcomeEnum.WIN:
                ranks = [0, 1]
                winning_team_ids, losing_team_ids = side_a_ids, side_b_ids
            else:
                ranks = [1, 0]
                winning_team_ids, losing_team_ids = side_b_ids, side_a_ids

            # 評分更新
            new_team1_ratings, new_team2_ratings = temp_env.rate(
                [team1_current_ratings, team2_current_ratings], ranks=ranks
            )

            # 合併結果
            final_ratings = {}
            for p_id, rating in {**new_team1_ratings, **new_team2_ratings}.items():
                final_ratings[p_id] = {"mu": rating.mu, "sigma": rating.sigma}

            # 應用性別調整
            RatingService._apply_gender_adjustments(
                final_ratings,
                winning_team_ids,
                losing_team_ids,
                all_match_players_data,
                base_ratings,
            )

            # 更新當前評分狀態
            for p_id, new_rating_values in final_ratings.items():
                current_ratings[p_id] = trueskill_env.create_rating(
                    mu=new_rating_values["mu"], sigma=new_rating_values["sigma"]
                )

        # 將最終評分寫入資料庫
        for p_id, final_rating in current_ratings.items():
            member = players_to_recalculate.get(p_id)
            if member:
                member.mu = final_rating.mu
                member.sigma = final_rating.sigma
