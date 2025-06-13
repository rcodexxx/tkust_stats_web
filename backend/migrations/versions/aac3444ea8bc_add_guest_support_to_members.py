# 修復 aac3444ea8bc_add_guest_support_to_members.py 文件

"""Add guest support to members

Revision ID: aac3444ea8bc
Revises: 22e266f04f94
Create Date: 2025-06-13 13:xx:xx.xxxxxx

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'aac3444ea8bc'
down_revision = '22e266f04f94'
branch_labels = None
depends_on = None


def upgrade():
    """添加訪客支援功能 - 生產環境安全版本"""

    print("開始添加訪客支援...")

    # 1. 修改 user_id 為可空
    print("步驟 1: 修改 user_id 為可空...")
    with op.batch_alter_table('members', schema=None) as batch_op:
        try:
            # 嘗試移除外鍵約束
            batch_op.drop_constraint('fk_members_user_id', type_='foreignkey')
        except Exception:
            # 如果約束名稱不同或不存在，忽略錯誤
            pass

        # 修改 user_id 為可空
        batch_op.alter_column('user_id',
                              existing_type=sa.INTEGER(),
                              nullable=True)

        # 重新添加外鍵約束
        batch_op.create_foreign_key('fk_members_user_id', 'users', ['user_id'], ['id'], ondelete='CASCADE')

    # 2. 添加訪客欄位（先設為可空）
    print("步驟 2: 添加訪客欄位...")
    with op.batch_alter_table('members', schema=None) as batch_op:
        # 先添加所有欄位為可空
        batch_op.add_column(sa.Column('is_guest', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('guest_phone', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('guest_identifier', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('created_by_user_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('last_used_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('usage_count', sa.Integer(), nullable=True))

    # 3. 為現有數據設置預設值
    print("步驟 3: 設置現有數據的預設值...")
    op.execute("UPDATE members SET is_guest = FALSE WHERE is_guest IS NULL")
    op.execute("UPDATE members SET usage_count = 0 WHERE usage_count IS NULL")

    # 4. 修改必要欄位為不可空
    print("步驟 4: 修改欄位約束...")
    with op.batch_alter_table('members', schema=None) as batch_op:
        batch_op.alter_column('is_guest',
                              existing_type=sa.Boolean(),
                              nullable=False)
        batch_op.alter_column('usage_count',
                              existing_type=sa.Integer(),
                              nullable=False)

    # 5. 添加索引和約束
    print("步驟 5: 添加索引和約束...")
    with op.batch_alter_table('members', schema=None) as batch_op:
        # 訪客識別碼唯一索引
        batch_op.create_index('ix_members_guest_identifier', ['guest_identifier'], unique=True)

        # 創建者外鍵
        batch_op.create_foreign_key('fk_members_created_by_user_id', 'users', ['created_by_user_id'], ['id'])

        # 訪客電話索引
        batch_op.create_index('ix_members_guest_phone', ['guest_phone'], unique=False)

        # 複合索引
        batch_op.create_index('ix_members_creator_guest', ['created_by_user_id', 'is_guest'], unique=False)

    print("✅ 訪客支援添加完成！")


def downgrade():
    """移除訪客支援功能"""

    print("開始移除訪客支援...")

    # 1. 刪除所有訪客記錄
    print("步驟 1: 刪除訪客記錄...")
    op.execute("DELETE FROM members WHERE is_guest = TRUE")

    # 2. 移除索引和約束
    print("步驟 2: 移除索引和約束...")
    with op.batch_alter_table('members', schema=None) as batch_op:
        try:
            batch_op.drop_index('ix_members_creator_guest')
            batch_op.drop_index('ix_members_guest_phone')
            batch_op.drop_index('ix_members_guest_identifier')
            batch_op.drop_constraint('fk_members_created_by_user_id', type_='foreignkey')
        except Exception as e:
            print(f"移除索引時出錯（可能已不存在）: {e}")

    # 3. 移除訪客相關欄位
    print("步驟 3: 移除訪客欄位...")
    with op.batch_alter_table('members', schema=None) as batch_op:
        batch_op.drop_column('usage_count')
        batch_op.drop_column('last_used_at')
        batch_op.drop_column('created_by_user_id')
        batch_op.drop_column('guest_identifier')
        batch_op.drop_column('guest_phone')
        batch_op.drop_column('is_guest')

    # 4. 恢復 user_id 為不可空
    print("步驟 4: 恢復 user_id 約束...")
    with op.batch_alter_table('members', schema=None) as batch_op:
        batch_op.drop_constraint('fk_members_user_id', type_='foreignkey')
        batch_op.alter_column('user_id',
                              existing_type=sa.INTEGER(),
                              nullable=False)
        batch_op.create_foreign_key('fk_members_user_id', 'users', ['user_id'], ['id'], ondelete='CASCADE')

    print("✅ 訪客支援移除完成！")
