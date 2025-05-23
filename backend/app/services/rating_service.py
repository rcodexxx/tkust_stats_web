from trueskill import Rating, rate_1vs1, rate
from ..models.enums import GenderEnum

GENDER_BONUS_MU = 0.7 # 女生打贏男生時，額外增加的 mu
GENDER_ADJUST_SIGMA = 0.5 # 女生對男生時，女生的 sigma 可以稍微調高一點點，表示結果更不可測 (可選)


def calculate_new_ratings_1v1(
    p1_mu, p1_sigma, p1_gender: GenderEnum,
    p2_mu, p2_sigma, p2_gender: GenderEnum,
    p1_won: bool
):
    """計算 1v1 比賽後的新 TrueSkill 評分，並加入性別調整。"""

    r1_initial = Rating(mu=p1_mu, sigma=p1_sigma)
    r2_initial = Rating(mu=p2_mu, sigma=p2_sigma)

    r1 = Rating(mu=p1_mu, sigma=p1_sigma)
    r2 = Rating(mu=p2_mu, sigma=p2_sigma)

    # 標準 TrueSkill 更新
    if p1_won:
        new_r1_base, new_r2_base = rate_1vs1(r1, r2)
    else:
        new_r2_base, new_r1_base = rate_1vs1(r2, r1)

    # 性別差異獎勵調整
    final_p1_mu, final_p1_sigma = new_r1_base.mu, new_r1_base.sigma
    final_p2_mu, final_p2_sigma = new_r2_base.mu, new_r2_base.sigma

    if p1_won: # P1 獲勝
        if p1_gender == GenderEnum.FEMALE and p2_gender == GenderEnum.MALE:
            final_p1_mu += GENDER_BONUS_MU
            print(f"Gender bonus applied to P1 (Female) for winning against Male. Mu +{GENDER_BONUS_MU}")
    else: # P2 獲勝
        if p2_gender == GenderEnum.FEMALE and p1_gender == GenderEnum.MALE:
            final_p2_mu += GENDER_BONUS_MU
            print(f"Gender bonus applied to P2 (Female) for winning against Male. Mu +{GENDER_BONUS_MU}")

    return ((final_p1_mu, final_p1_sigma), (final_p2_mu, final_p2_sigma))


def calculate_new_ratings_2v2(
        t1p1_mu, t1p1_sigma, t1p1_gender: GenderEnum,
        t1p2_mu, t1p2_sigma, t1p2_gender: GenderEnum,
        t2p1_mu, t2p1_sigma, t2p1_gender: GenderEnum,
        t2p2_mu, t2p2_sigma, t2p2_gender: GenderEnum,
        team1_won: bool  # True 表示 team1 (t1p1, t1p2) 獲勝
):
    """
    計算 2v2 (雙打) 比賽後的新 TrueSkill 評分。
    如果 team1 獲勝，且 team1 中有女性，且 team2 中有男性，則 team1 中的女性獲得額外 mu 獎勵。
    """
    t1p1_r = Rating(mu=t1p1_mu, sigma=t1p1_sigma)
    t1p2_r = Rating(mu=t1p2_mu, sigma=t1p2_sigma)
    t2p1_r = Rating(mu=t2p1_mu, sigma=t2p1_sigma)
    t2p2_r = Rating(mu=t2p2_mu, sigma=t2p2_sigma)

    team1_ratings_obj = [t1p1_r, t1p2_r]
    team2_ratings_obj = [t2p1_r, t2p2_r]

    # 標準 TrueSkill 更新
    if team1_won:
        # Team 1 won (rank 0), Team 2 lost (rank 1)
        (new_team1_base_ratings, new_team2_base_ratings) = rate([team1_ratings_obj, team2_ratings_obj], ranks=[0, 1])
    else:
        # Team 2 won (rank 0), Team 1 lost (rank 1)
        (new_team2_base_ratings, new_team1_base_ratings) = rate([team2_ratings_obj, team1_ratings_obj], ranks=[0, 1])

    # 將更新後的 mu, sigma 先取出來
    # Team 1 players
    t1p1_new_mu, t1p1_new_sigma = new_team1_base_ratings[0].mu, new_team1_base_ratings[0].sigma
    t1p2_new_mu, t1p2_new_sigma = new_team1_base_ratings[1].mu, new_team1_base_ratings[1].sigma
    # Team 2 players
    t2p1_new_mu, t2p1_new_sigma = new_team2_base_ratings[0].mu, new_team2_base_ratings[0].sigma
    t2p2_new_mu, t2p2_new_sigma = new_team2_base_ratings[1].mu, new_team2_base_ratings[1].sigma

    # 根據需求進行性別獎勵調整
    if team1_won:
        team1_has_female = (t1p1_gender == GenderEnum.FEMALE or t1p2_gender == GenderEnum.FEMALE)
        team2_has_male = (t2p1_gender == GenderEnum.MALE or t2p2_gender == GenderEnum.MALE)

        if team1_has_female and team2_has_male:
            if t1p1_gender == GenderEnum.FEMALE:
                t1p1_new_mu += GENDER_BONUS_MU
            if t1p2_gender == GenderEnum.FEMALE:
                t1p2_new_mu += GENDER_BONUS_MU

    return (
        (t1p1_new_mu, t1p1_new_sigma), (t1p2_new_mu, t1p2_new_sigma),  # Team 1 new ratings
        (t2p1_new_mu, t2p1_new_sigma), (t2p2_new_mu, t2p2_new_sigma)  # Team 2 new ratings
    )