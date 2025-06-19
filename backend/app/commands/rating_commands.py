# backend/app/commands/rating_commands.py
"""
評分系統管理命令

提供重新計算評分、重置評分等功能的 CLI 指令。
"""

import click
from flask import current_app
from flask.cli import with_appcontext
from sqlalchemy import func

from ..extensions import db
from ..models import MatchRecord, Member
from ..services.rating_service import RatingService, trueskill_env


@click.command("recalculate-all-ratings")
@click.option("--force", is_flag=True, help="強制執行，不詢問確認")
@click.option("--batch-size", default=50, help="批次處理大小（默認50個球員為一批）")
@click.option("--dry-run", is_flag=True, help="試運行模式，不實際修改數據庫")
@with_appcontext
def recalculate_all_ratings_command(force, batch_size, dry_run):
    """
    重新計算所有球員的積分

    這個指令會：
    1. 重置所有球員的 mu 和 sigma 值為初始值
    2. 按時間順序重新處理所有比賽記錄
    3. 重新計算每位球員的評分

    注意：這個操作不可逆，建議在執行前備份數據庫。
    """
    click.echo(click.style("🎾 軟式網球積分重計算工具", fg="blue", bold=True))
    click.echo("=" * 50)

    # 統計信息
    total_members = Member.query.count()
    total_matches = MatchRecord.query.count()

    if total_members == 0:
        click.echo(click.style("❌ 沒有找到任何球員記錄", fg="red"))
        return

    click.echo("📊 系統統計：")
    click.echo(f"   總球員數量: {total_members}")
    click.echo(f"   總比賽記錄: {total_matches}")
    click.echo(f"   批次大小: {batch_size}")

    if dry_run:
        click.echo(click.style("🔍 試運行模式 - 不會修改數據庫", fg="yellow"))

    # 確認操作
    if not force and not dry_run:
        click.echo("\n⚠️  警告：此操作將重置所有球員的積分並重新計算！")
        click.echo("   建議在執行前備份數據庫。")
        if not click.confirm("確定要繼續嗎？"):
            click.echo("操作已取消")
            return

    click.echo("\n🚀 開始重新計算積分...")

    try:
        # 獲取所有球員ID，分批處理
        all_member_ids = db.session.query(Member.id).all()
        all_member_ids = [member_id[0] for member_id in all_member_ids]

        if not all_member_ids:
            click.echo(click.style("❌ 沒有找到任何球員", fg="red"))
            return

        # 分批處理
        total_batches = (len(all_member_ids) + batch_size - 1) // batch_size
        success_count = 0
        error_count = 0

        for i in range(0, len(all_member_ids), batch_size):
            batch_ids = all_member_ids[i : i + batch_size]
            batch_num = (i // batch_size) + 1

            click.echo(
                f"\n📦 處理批次 {batch_num}/{total_batches} ({len(batch_ids)} 個球員)"
            )

            try:
                if not dry_run:
                    # 實際執行重計算
                    RatingService.recalculate_ratings_for_players(batch_ids)
                    db.session.commit()
                    success_count += len(batch_ids)
                    click.echo(click.style(f"   ✅ 批次 {batch_num} 完成", fg="green"))
                else:
                    # 試運行模式，只顯示會處理哪些球員
                    members = Member.query.filter(Member.id.in_(batch_ids)).all()
                    for member in members:
                        click.echo(
                            f"   🔍 會處理: {member.display_name} (ID: {member.id})"
                        )
                    success_count += len(batch_ids)

            except Exception as e:
                error_count += len(batch_ids)
                click.echo(
                    click.style(f"   ❌ 批次 {batch_num} 失敗: {str(e)}", fg="red")
                )
                current_app.logger.error(f"批次 {batch_num} 重計算失敗: {e}")

                if not dry_run:
                    # 回滾這個批次的更改
                    db.session.rollback()

        # 完成統計
        click.echo("\n" + "=" * 50)
        if dry_run:
            click.echo(click.style("🔍 試運行完成！", fg="blue", bold=True))
            click.echo(f"   將會處理 {success_count} 個球員")
            if error_count > 0:
                click.echo(f"   可能有問題的球員: {error_count}")
        else:
            click.echo(click.style("🎉 積分重計算完成！", fg="green", bold=True))
            click.echo(f"   成功處理: {success_count} 個球員")
            if error_count > 0:
                click.echo(f"   處理失敗: {error_count} 個球員")

        # 顯示重計算後的統計
        if not dry_run and success_count > 0:
            _show_rating_statistics()

    except Exception as e:
        click.echo(click.style(f"❌ 重計算過程中發生錯誤: {str(e)}", fg="red"))
        current_app.logger.error(f"積分重計算失敗: {e}")
        if not dry_run:
            db.session.rollback()


@click.command("reset-all-ratings")
@click.option("--force", is_flag=True, help="強制執行，不詢問確認")
@click.option("--dry-run", is_flag=True, help="試運行模式，不實際修改數據庫")
@with_appcontext
def reset_all_ratings_command(force, dry_run):
    """
    重置所有球員的積分為初始值

    將所有球員的 mu 和 sigma 重置為 TrueSkill 初始值
    """
    click.echo(click.style("🔄 重置所有積分為初始值", fg="blue", bold=True))

    total_members = Member.query.count()

    if total_members == 0:
        click.echo(click.style("❌ 沒有找到任何球員記錄", fg="red"))
        return

    click.echo(f"📊 將重置 {total_members} 個球員的積分")
    click.echo(f"   初始 μ 值: {trueskill_env.mu}")
    click.echo(f"   初始 σ 值: {trueskill_env.sigma}")

    if dry_run:
        click.echo(click.style("🔍 試運行模式 - 不會修改數據庫", fg="yellow"))

    if not force and not dry_run:
        if not click.confirm("確定要重置所有球員的積分嗎？"):
            click.echo("操作已取消")
            return

    try:
        if not dry_run:
            # 實際重置
            Member.query.update(
                {Member.mu: trueskill_env.mu, Member.sigma: trueskill_env.sigma}
            )
            db.session.commit()
            click.echo(
                click.style(f"✅ 已重置 {total_members} 個球員的積分", fg="green")
            )
        else:
            click.echo(
                click.style(
                    f"🔍 試運行：將會重置 {total_members} 個球員的積分", fg="blue"
                )
            )

    except Exception as e:
        click.echo(click.style(f"❌ 重置失敗: {str(e)}", fg="red"))
        current_app.logger.error(f"積分重置失敗: {e}")
        if not dry_run:
            db.session.rollback()


@click.command("rating-stats")
@with_appcontext
def rating_stats_command():
    """顯示當前評分系統統計信息"""
    click.echo(click.style("📊 TrueSkill 評分系統統計", fg="blue", bold=True))
    _show_rating_statistics()


def _show_rating_statistics():
    """顯示評分統計信息"""
    try:
        # 基本統計
        stats = db.session.query(
            func.count(Member.id).label("total"),
            func.avg(Member.mu).label("avg_mu"),
            func.avg(Member.sigma).label("avg_sigma"),
            func.min(Member.mu).label("min_mu"),
            func.max(Member.mu).label("max_mu"),
            func.min(Member.sigma).label("min_sigma"),
            func.max(Member.sigma).label("max_sigma"),
        ).first()

        if stats.total == 0:
            click.echo("❌ 沒有球員數據")
            return

        # 計算保守評分統計
        conservative_stats = db.session.query(
            func.avg(Member.mu - 3 * Member.sigma).label("avg_conservative"),
            func.min(Member.mu - 3 * Member.sigma).label("min_conservative"),
            func.max(Member.mu - 3 * Member.sigma).label("max_conservative"),
        ).first()

        click.echo("=" * 50)
        click.echo(f"總球員數量: {stats.total}")
        click.echo(
            f"μ 值統計: 平均 {stats.avg_mu:.2f}, 範圍 {stats.min_mu:.2f} - {stats.max_mu:.2f}"
        )
        click.echo(
            f"σ 值統計: 平均 {stats.avg_sigma:.2f}, 範圍 {stats.min_sigma:.2f} - {stats.max_sigma:.2f}"
        )
        click.echo(
            f"保守評分: 平均 {conservative_stats.avg_conservative:.2f}, 範圍 {conservative_stats.min_conservative:.2f} - {conservative_stats.max_conservative:.2f}"
        )

        # 經驗等級分布（使用簡單的分別查詢方式）
        newbie_count = Member.query.filter(Member.sigma >= 7.0).count()
        beginner_count = Member.query.filter(Member.sigma.between(5.0, 6.99)).count()
        intermediate_count = Member.query.filter(
            Member.sigma.between(3.0, 4.99)
        ).count()
        advanced_count = Member.query.filter(Member.sigma.between(2.0, 2.99)).count()
        expert_count = Member.query.filter(Member.sigma < 2.0).count()

        click.echo("\n經驗等級分布:")
        click.echo(f"  新手 (σ ≥ 7.0): {newbie_count}")
        click.echo(f"  初級 (5.0 ≤ σ < 7.0): {beginner_count}")
        click.echo(f"  中級 (3.0 ≤ σ < 5.0): {intermediate_count}")
        click.echo(f"  高級 (2.0 ≤ σ < 3.0): {advanced_count}")
        click.echo(f"  資深 (σ < 2.0): {expert_count}")

        # 顯示排名前5的球員
        top_players = (
            db.session.query(Member)
            .order_by((Member.mu - 3 * Member.sigma).desc())
            .limit(5)
            .all()
        )

        if top_players:
            click.echo("\n🏆 排名前5的球員:")
            for i, player in enumerate(top_players, 1):
                conservative_score = player.mu - 3 * player.sigma
                click.echo(
                    f"  {i}. {player.display_name}: {conservative_score:.2f} (μ={player.mu:.2f}, σ={player.sigma:.2f})"
                )

    except Exception as e:
        click.echo(click.style(f"❌ 獲取統計信息失敗: {str(e)}", fg="red"))
        current_app.logger.error(f"獲取評分統計失敗: {e}")


@click.command("validate-ratings")
@with_appcontext
def validate_ratings_command():
    """驗證評分數據的完整性"""
    click.echo(click.style("🔍 驗證評分數據完整性", fg="blue", bold=True))

    issues = []

    try:
        # 檢查異常的 mu 值
        abnormal_mu = Member.query.filter((Member.mu < 0) | (Member.mu > 100)).count()

        if abnormal_mu > 0:
            issues.append(f"發現 {abnormal_mu} 個球員的 μ 值異常（< 0 或 > 100）")

        # 檢查異常的 sigma 值
        abnormal_sigma = Member.query.filter(
            (Member.sigma < 0) | (Member.sigma > 25)
        ).count()

        if abnormal_sigma > 0:
            issues.append(f"發現 {abnormal_sigma} 個球員的 σ 值異常（< 0 或 > 25）")

        # 檢查 NULL 值
        null_ratings = Member.query.filter(
            (Member.mu.is_(None)) | (Member.sigma.is_(None))
        ).count()

        if null_ratings > 0:
            issues.append(f"發現 {null_ratings} 個球員的評分為空值")

        # 顯示結果
        if issues:
            click.echo(click.style("⚠️  發現以下問題：", fg="yellow"))
            for issue in issues:
                click.echo(f"  - {issue}")
        else:
            click.echo(click.style("✅ 評分數據完整性檢查通過", fg="green"))

    except Exception as e:
        click.echo(click.style(f"❌ 驗證過程中發生錯誤: {str(e)}", fg="red"))
        current_app.logger.error(f"評分驗證失敗: {e}")
