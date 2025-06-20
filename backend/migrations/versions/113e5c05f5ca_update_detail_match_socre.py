"""add game scores and expand player stats

Revision ID: 113e5c05f5ca
Revises: 36304397c75b
Create Date: 2025-06-20 05:44:32.295992

"""

import sqlalchemy as sa
from alembic import op

revision = "113e5c05f5ca"
down_revision = "36304397c75b"
branch_labels = None
depends_on = None


def upgrade():
    # 添加每局比分欄位到 match_records 表
    with op.batch_alter_table("match_records", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "game1_a_score", sa.Integer(), nullable=True, comment="第1局A方得分"
            )
        )
        batch_op.add_column(
            sa.Column(
                "game1_b_score", sa.Integer(), nullable=True, comment="第1局B方得分"
            )
        )
        batch_op.add_column(
            sa.Column(
                "game2_a_score", sa.Integer(), nullable=True, comment="第2局A方得分"
            )
        )
        batch_op.add_column(
            sa.Column(
                "game2_b_score", sa.Integer(), nullable=True, comment="第2局B方得分"
            )
        )
        batch_op.add_column(
            sa.Column(
                "game3_a_score", sa.Integer(), nullable=True, comment="第3局A方得分"
            )
        )
        batch_op.add_column(
            sa.Column(
                "game3_b_score", sa.Integer(), nullable=True, comment="第3局B方得分"
            )
        )
        batch_op.add_column(
            sa.Column(
                "game4_a_score", sa.Integer(), nullable=True, comment="第4局A方得分"
            )
        )
        batch_op.add_column(
            sa.Column(
                "game4_b_score", sa.Integer(), nullable=True, comment="第4局B方得分"
            )
        )
        batch_op.add_column(
            sa.Column(
                "game5_a_score", sa.Integer(), nullable=True, comment="第5局A方得分"
            )
        )
        batch_op.add_column(
            sa.Column(
                "game5_b_score", sa.Integer(), nullable=True, comment="第5局B方得分"
            )
        )
        batch_op.add_column(
            sa.Column(
                "game6_a_score", sa.Integer(), nullable=True, comment="第6局A方得分"
            )
        )
        batch_op.add_column(
            sa.Column(
                "game6_b_score", sa.Integer(), nullable=True, comment="第6局B方得分"
            )
        )
        batch_op.add_column(
            sa.Column(
                "game7_a_score", sa.Integer(), nullable=True, comment="第7局A方得分"
            )
        )
        batch_op.add_column(
            sa.Column(
                "game7_b_score", sa.Integer(), nullable=True, comment="第7局B方得分"
            )
        )
        batch_op.add_column(
            sa.Column(
                "game8_a_score", sa.Integer(), nullable=True, comment="第8局A方得分"
            )
        )
        batch_op.add_column(
            sa.Column(
                "game8_b_score", sa.Integer(), nullable=True, comment="第8局B方得分"
            )
        )
        batch_op.add_column(
            sa.Column(
                "game9_a_score", sa.Integer(), nullable=True, comment="第9局A方得分"
            )
        )
        batch_op.add_column(
            sa.Column(
                "game9_b_score", sa.Integer(), nullable=True, comment="第9局B方得分"
            )
        )

    # 擴展 player_stats 表
    with op.batch_alter_table("player_stats", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "points_won", sa.Integer(), nullable=True, default=0, comment="總得分"
            )
        )
        batch_op.add_column(
            sa.Column(
                "additional_stats",
                sa.JSON(),
                nullable=True,
                comment="額外統計數據(JSON格式)",
            )
        )
        batch_op.add_column(
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
                comment="創建時間",
            )
        )
        batch_op.add_column(
            sa.Column(
                "updated_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
                comment="更新時間",
            )
        )

    # 為 player_stats 添加唯一約束
    with op.batch_alter_table("player_stats", schema=None) as batch_op:
        batch_op.create_unique_constraint(
            "uq_player_stats_match_member", ["match_record_id", "member_id"]
        )


def downgrade():
    # 移除 player_stats 的約束和欄位
    with op.batch_alter_table("player_stats", schema=None) as batch_op:
        batch_op.drop_constraint("uq_player_stats_match_member", type_="unique")
        batch_op.drop_column("updated_at")
        batch_op.drop_column("created_at")
        batch_op.drop_column("additional_stats")
        batch_op.drop_column("points_won")

    # 移除 match_records 的每局比分欄位
    with op.batch_alter_table("match_records", schema=None) as batch_op:
        batch_op.drop_column("game9_b_score")
        batch_op.drop_column("game9_a_score")
        batch_op.drop_column("game8_b_score")
        batch_op.drop_column("game8_a_score")
        batch_op.drop_column("game7_b_score")
        batch_op.drop_column("game7_a_score")
        batch_op.drop_column("game6_b_score")
        batch_op.drop_column("game6_a_score")
        batch_op.drop_column("game5_b_score")
        batch_op.drop_column("game5_a_score")
        batch_op.drop_column("game4_b_score")
        batch_op.drop_column("game4_a_score")
        batch_op.drop_column("game3_b_score")
        batch_op.drop_column("game3_a_score")
        batch_op.drop_column("game2_b_score")
        batch_op.drop_column("game2_a_score")
        batch_op.drop_column("game1_b_score")
        batch_op.drop_column("game1_a_score")
