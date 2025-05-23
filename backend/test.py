import random
from trueskill import Rating
from app.services.rating_service import calculate_new_ratings_2v2
from app.models.enums import GenderEnum

# 初始參數
PLAYER_COUNT = 15
FEMALE_COUNT = 6
MATCH_COUNT = 1000

class Player:
    def __init__(self, id, gender):
        self.id = id
        self.gender = gender
        self.mu = 25.0
        self.sigma = 25.0 / 3

    def update(self, mu, sigma):
        self.mu = mu
        self.sigma = sigma

    def score(self):
        return int((self.mu - 3 * self.sigma) * 100)

    def __repr__(self):
        return f"Player {self.id:2d} | {self.gender.name:6s} | mu: {self.mu:.2f} | σ: {self.sigma:.2f} | score: {self.score()}"

# 建立選手
players = [
    Player(i, GenderEnum.FEMALE if i < FEMALE_COUNT else GenderEnum.MALE)
    for i in range(PLAYER_COUNT)
]

def pick_random_teams():
    selected = random.sample(players, 4)
    return selected[:2], selected[2:]

# 模擬比賽
for _ in range(MATCH_COUNT):
    team1, team2 = pick_random_teams()
    team1_won = random.choice([True, False])

    result = calculate_new_ratings_2v2(
        team1[0].mu, team1[0].sigma, team1[0].gender,
        team1[1].mu, team1[1].sigma, team1[1].gender,
        team2[0].mu, team2[0].sigma, team2[0].gender,
        team2[1].mu, team2[1].sigma, team2[1].gender,
        team1_won
    )

    # 更新分數
    team1[0].update(*result[0])
    team1[1].update(*result[1])
    team2[0].update(*result[2])
    team2[1].update(*result[3])

# 結果排序輸出
players.sort(key=lambda p: p.score(), reverse=True)
print("\n🏆 Final Ranking After 1000 Matches:")
for p in players:
    print(p)