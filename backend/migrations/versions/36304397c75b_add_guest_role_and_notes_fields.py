"""add guest role and notes fields

Revision ID: 36304397c75b
Revises: aac3444ea8bc
Create Date: 2025-06-15 [當前時間]

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "36304397c75b"
down_revision = "aac3444ea8bc"
branch_labels = None
depends_on = None


def upgrade():
    """添加訪客身份類型和備註欄位 - PostgreSQL 版本"""

    print("🚀 開始添加訪客身份類型和備註欄位（PostgreSQL）...")

    # 1. 創建枚舉類型（PostgreSQL 必須先創建枚舉類型）
    print("步驟 1/6: 創建 guest_role_enum 枚舉類型...")
    guest_role_enum = postgresql.ENUM(
        "teammate", "opponent", "substitute", "neutral", name="guest_role_enum"
    )
    guest_role_enum.create(op.get_bind())
    print("✅ guest_role_enum 枚舉類型創建成功")

    # 2. 添加 guest_role 欄位
    print("步驟 2/6: 添加 guest_role 欄位...")
    op.add_column(
        "members",
        sa.Column(
            "guest_role",
            guest_role_enum,
            nullable=True,
            comment="訪客在比賽中的身份類型",
        ),
    )
    print("✅ guest_role 欄位添加成功")

    # 3. 添加 guest_notes 欄位
    print("步驟 3/6: 添加 guest_notes 欄位...")
    op.add_column(
        "members",
        sa.Column(
            "guest_notes",
            sa.Text(),
            nullable=True,
            comment="訪客備註（如：來自哪個學校、特殊說明等）",
        ),
    )
    print("✅ guest_notes 欄位添加成功")

    # 4. 為現有訪客設置預設值
    print("步驟 4/6: 為現有訪客設置預設值...")
    try:
        # 檢查是否有現有訪客
        connection = op.get_bind()
        result = connection.execute(
            sa.text("SELECT COUNT(*) FROM members WHERE is_guest = true")
        )
        guest_count = result.scalar()

        if guest_count > 0:
            print(f"發現 {guest_count} 個現有訪客，設置預設身份為 'neutral'")
            # 為現有訪客設置預設身份
            connection.execute(
                sa.text(
                    "UPDATE members SET guest_role = 'neutral' WHERE is_guest = true AND guest_role IS NULL"
                )
            )
            print("✅ 現有訪客預設值設置完成")
        else:
            print("✅ 沒有現有訪客，跳過預設值設置")
    except Exception as e:
        print(f"⚠️  設置預設值時出現警告: {e}")

    # 5. 添加索引
    print("步驟 5/6: 添加索引...")
    op.create_index("ix_members_guest_role", "members", ["guest_role"])
    print("✅ guest_role 索引添加成功")

    # 6. 檢查並修復可能缺失的索引（解決歷史問題）
    print("步驟 6/6: 檢查並創建可能缺失的索引...")
    try:
        # 檢查是否存在 guest_identifier 唯一索引
        inspector = sa.inspect(op.get_bind())
        existing_indexes = [idx["name"] for idx in inspector.get_indexes("members")]

        if "ix_members_guest_identifier" not in existing_indexes:
            print("創建缺失的 guest_identifier 索引...")
            op.create_index(
                "ix_members_guest_identifier",
                "members",
                ["guest_identifier"],
                unique=True,
            )

        if "ix_members_guest_phone" not in existing_indexes:
            print("創建缺失的 guest_phone 索引...")
            op.create_index("ix_members_guest_phone", "members", ["guest_phone"])

        if "ix_members_creator_guest" not in existing_indexes:
            print("創建缺失的 creator_guest 複合索引...")
            op.create_index(
                "ix_members_creator_guest",
                "members",
                ["created_by_user_id", "is_guest"],
            )

        print("✅ 索引檢查和修復完成")
    except Exception as e:
        print(f"⚠️  索引檢查時出現警告: {e}")

    print("🎉 訪客身份類型和備註欄位添加完成！")
    print("📋 新增內容總結:")
    print("   - guest_role_enum: PostgreSQL 枚舉類型")
    print("   - guest_role: 訪客身份類型欄位")
    print("   - guest_notes: 訪客備註欄位")
    print("   - ix_members_guest_role: guest_role 索引")


def downgrade():
    """移除訪客身份類型和備註欄位 - PostgreSQL 版本"""

    print("🔄 開始移除訪客身份類型和備註欄位（PostgreSQL）...")

    # 1. 安全地移除索引
    print("步驟 1/5: 移除索引...")

    # 獲取現有索引列表，只刪除存在的索引
    try:
        inspector = sa.inspect(op.get_bind())
        existing_indexes = [idx["name"] for idx in inspector.get_indexes("members")]

        indexes_to_remove = [
            "ix_members_guest_role",
            "ix_members_creator_guest",
            "ix_members_guest_phone",
            "ix_members_guest_identifier",
        ]

        for index_name in indexes_to_remove:
            if index_name in existing_indexes:
                print(f"移除索引: {index_name}")
                op.drop_index(index_name, table_name="members")
            else:
                print(f"跳過不存在的索引: {index_name}")

        print("✅ 索引移除完成")
    except Exception as e:
        print(f"⚠️  移除索引時出現警告: {e}")

    # 2. 移除 guest_notes 欄位
    print("步驟 2/5: 移除 guest_notes 欄位...")
    try:
        op.drop_column("members", "guest_notes")
        print("✅ guest_notes 欄位移除成功")
    except Exception as e:
        print(f"⚠️  移除 guest_notes 欄位時出現警告: {e}")

    # 3. 移除 guest_role 欄位
    print("步驟 3/5: 移除 guest_role 欄位...")
    try:
        op.drop_column("members", "guest_role")
        print("✅ guest_role 欄位移除成功")
    except Exception as e:
        print(f"⚠️  移除 guest_role 欄位時出現警告: {e}")

    # 4. 移除枚舉類型（PostgreSQL）
    print("步驟 4/5: 移除 guest_role_enum 枚舉類型...")
    try:
        guest_role_enum = postgresql.ENUM(name="guest_role_enum")
        guest_role_enum.drop(op.get_bind())
        print("✅ guest_role_enum 枚舉類型移除成功")
    except Exception as e:
        print(f"⚠️  移除枚舉類型時出現警告: {e}")

    # 5. 驗證回滾
    print("步驟 5/5: 驗證回滾結果...")
    try:
        inspector = sa.inspect(op.get_bind())
        columns = [col["name"] for col in inspector.get_columns("members")]

        removed_columns = []
        if "guest_role" not in columns:
            removed_columns.append("guest_role")
        if "guest_notes" not in columns:
            removed_columns.append("guest_notes")

        if len(removed_columns) == 2:
            print("✅ 所有訪客相關欄位已移除")
        else:
            print(
                f"⚠️  部分欄位可能未完全移除: {set(['guest_role', 'guest_notes']) - set(removed_columns)}"
            )

    except Exception as e:
        print(f"⚠️  驗證回滾時出現警告: {e}")

    print("🔄 訪客身份類型和備註欄位移除完成！")
