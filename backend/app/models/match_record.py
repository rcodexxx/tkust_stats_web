# backend/app/models/match_record.py
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import relationship

from ..extensions import db
from .enums import MatchOutcomeEnum


class MatchRecord(db.Model):
    __tablename__ = "match_records"

    id = db.Column(Integer, primary_key=True, comment="比賽記錄唯一識別碼")

    match_id = db.Column(
        Integer,
        ForeignKey("matches.id", name="fk_match_records_match_id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="所屬比賽事件ID",
    )
    match = relationship("Match", back_populates="results")

    # --- Side A Players ---
    player1_id = db.Column(
        Integer,
        ForeignKey("members.id", name="fk_match_records_p1_id", ondelete="SET NULL"),
        nullable=False,
        index=True,
    )
    player1 = relationship(
        "Member", foreign_keys=[player1_id], backref="match_records_p1"
    )

    player2_id = db.Column(
        Integer,
        ForeignKey("members.id", name="fk_match_records_p2_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    player2 = relationship(
        "Member", foreign_keys=[player2_id], backref="match_records_p2"
    )

    # --- Side B Players ---
    player3_id = db.Column(
        Integer,
        ForeignKey("members.id", name="fk_match_records_p3_id", ondelete="SET NULL"),
        nullable=False,
        index=True,
    )
    player3 = relationship(
        "Member", foreign_keys=[player3_id], backref="match_records_p3"
    )

    player4_id = db.Column(
        Integer,
        ForeignKey("members.id", name="fk_match_records_p4_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    player4 = relationship(
        "Member", foreign_keys=[player4_id], backref="match_records_p4"
    )

    # --- Scores and Outcome ---
    a_games = db.Column(Integer, nullable=False, comment="A方贏得的總局數")
    b_games = db.Column(Integer, nullable=False, comment="B方贏得的總局數")

    # 記錄 A 方的賽果
    side_a_outcome = db.Column(
        SQLAlchemyEnum(
            MatchOutcomeEnum,
            name="outcome_enum_match_records",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        comment="A方視角的比賽結果 (勝/負)",
    )

    # --- 🔥 新增：每局詳細比分欄位 ---
    # 第1局比分
    game1_a_score = db.Column(Integer, nullable=True, default=0, comment="第1局A方得分")
    game1_b_score = db.Column(Integer, nullable=True, default=0, comment="第1局B方得分")

    # 第2局比分
    game2_a_score = db.Column(Integer, nullable=True, default=0, comment="第2局A方得分")
    game2_b_score = db.Column(Integer, nullable=True, default=0, comment="第2局B方得分")

    # 第3局比分
    game3_a_score = db.Column(Integer, nullable=True, default=0, comment="第3局A方得分")
    game3_b_score = db.Column(Integer, nullable=True, default=0, comment="第3局B方得分")

    # 第4局比分
    game4_a_score = db.Column(Integer, nullable=True, default=0, comment="第4局A方得分")
    game4_b_score = db.Column(Integer, nullable=True, default=0, comment="第4局B方得分")

    # 第5局比分
    game5_a_score = db.Column(Integer, nullable=True, default=0, comment="第5局A方得分")
    game5_b_score = db.Column(Integer, nullable=True, default=0, comment="第5局B方得分")

    # 第6局比分
    game6_a_score = db.Column(Integer, nullable=True, default=0, comment="第6局A方得分")
    game6_b_score = db.Column(Integer, nullable=True, default=0, comment="第6局B方得分")

    # 第7局比分
    game7_a_score = db.Column(Integer, nullable=True, default=0, comment="第7局A方得分")
    game7_b_score = db.Column(Integer, nullable=True, default=0, comment="第7局B方得分")

    # 第8局比分
    game8_a_score = db.Column(Integer, nullable=True, default=0, comment="第8局A方得分")
    game8_b_score = db.Column(Integer, nullable=True, default=0, comment="第8局B方得分")

    # 第9局比分
    game9_a_score = db.Column(Integer, nullable=True, default=0, comment="第9局A方得分")
    game9_b_score = db.Column(Integer, nullable=True, default=0, comment="第9局B方得分")

    # --- 關聯到選手統計（保留）---
    player_stats_entries = relationship(
        "PlayerStats", back_populates="match_record", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<MatchRecord id={self.id}, {self.a_games}-{self.b_games}>"

    # --- 🔥 新增：每局比分便利方法 ---

    def get_game_score(self, game_number: int) -> tuple[int, int]:
        """
        獲取指定局數的比分

        Args:
            game_number: 局數 (1-9)

        Returns:
            tuple: (A方得分, B方得分)
        """
        if not (1 <= game_number <= 9):
            return (0, 0)

        a_score_attr = f"game{game_number}_a_score"
        b_score_attr = f"game{game_number}_b_score"

        a_score = getattr(self, a_score_attr, 0) or 0
        b_score = getattr(self, b_score_attr, 0) or 0

        return (a_score, b_score)

    def set_game_score(self, game_number: int, a_score: int, b_score: int) -> None:
        """
        設置指定局數的比分

        Args:
            game_number: 局數 (1-9)
            a_score: A方得分
            b_score: B方得分
        """
        if not (1 <= game_number <= 9):
            return

        a_score_attr = f"game{game_number}_a_score"
        b_score_attr = f"game{game_number}_b_score"

        setattr(self, a_score_attr, a_score)
        setattr(self, b_score_attr, b_score)

    def get_all_games_scores(self) -> list[dict]:
        """
        獲取所有局的比分詳情

        Returns:
            list: [{"game": 1, "a_score": 11, "b_score": 9, "winner": "A"}, ...]
        """
        games = []
        for game_num in range(1, 10):
            a_score, b_score = self.get_game_score(game_num)

            # 只返回有進行的局（雙方得分不全為0）
            if a_score > 0 or b_score > 0:
                winner = None
                if a_score > b_score:
                    winner = "A"
                elif b_score > a_score:
                    winner = "B"

                games.append(
                    {
                        "game": game_num,
                        "a_score": a_score,
                        "b_score": b_score,
                        "winner": winner,
                        "is_completed": winner is not None,
                    }
                )

        return games

    def calculate_games_won(self) -> tuple[int, int]:
        """
        根據每局比分計算總局數

        Returns:
            tuple: (A方贏得局數, B方贏得局數)
        """
        a_games_won = 0
        b_games_won = 0

        for game_num in range(1, 10):
            a_score, b_score = self.get_game_score(game_num)

            if a_score > b_score and a_score > 0:
                a_games_won += 1
            elif b_score > a_score and b_score > 0:
                b_games_won += 1

        return (a_games_won, b_games_won)

    def update_games_total(self) -> None:
        """
        根據每局詳細比分自動更新 a_games 和 b_games
        """
        a_total, b_total = self.calculate_games_won()
        self.a_games = a_total
        self.b_games = b_total

        # 更新比賽結果
        if a_total > b_total:
            self.side_a_outcome = MatchOutcomeEnum.WIN
        else:
            self.side_a_outcome = MatchOutcomeEnum.LOSS

    def is_match_completed(self, match_format: str = "games_9") -> bool:
        """
        判斷比賽是否結束

        Args:
            match_format: 比賽制度 ('games_5', 'games_7', 'games_9')

        Returns:
            bool: 比賽是否結束
        """
        format_map = {
            "games_5": 3,
            "games_7": 4,
            "games_9": 5,
        }

        required_games = format_map.get(match_format, 5)
        a_total, b_total = self.calculate_games_won()

        return a_total >= required_games or b_total >= required_games

    def has_detailed_scores(self) -> bool:
        """
        檢查是否有詳細比分記錄

        Returns:
            bool: 是否有任何局的詳細比分
        """
        for game_num in range(1, 10):
            a_score, b_score = self.get_game_score(game_num)
            if a_score > 0 or b_score > 0:
                return True
        return False

    # --- 原有方法保持不變 ---

    def get_all_players(self) -> list:
        """
        獲取參與該比賽的所有選手

        Returns:
            list: 參與比賽的選手列表
        """
        players = []
        if self.player1:
            players.append(self.player1)
        if self.player2:
            players.append(self.player2)
        if self.player3:
            players.append(self.player3)
        if self.player4:
            players.append(self.player4)
        return players

    def get_player_stats_detail(self) -> list:
        """
        獲取所有選手的統計詳情

        Returns:
            list: 每個選手統計的字典列表
        """
        return [stat.to_dict() for stat in self.player_stats]

    def to_dict_with_details(self) -> dict:
        """
        轉換為包含詳細信息的字典

        Returns:
            dict: 完整的比賽記錄字典
        """
        return {
            "id": self.id,
            "match_id": self.match_id,
            "a_games": self.a_games,
            "b_games": self.b_games,
            "side_a_outcome": self.side_a_outcome.value
            if self.side_a_outcome
            else None,
            "players": [player.name for player in self.get_all_players()],
            "has_detailed_scores": self.has_detailed_scores(),
            "games_detail": self.get_all_games_scores(),
            "player_stats": self.get_player_stats_detail(),
        }
