# backend/app/commands/__init__.py
from flask import Blueprint

from .init_admin import (
    init_admin_command,
    list_admins_command,
    reset_admin_password_command,
)
from .rating_commands import (
    rating_stats_command,
    recalculate_all_ratings_command,
    reset_all_ratings_command,
    validate_ratings_command,
)

# 創建一個 Blueprint 來組織命令
# cli_group=None 表示指令直接在 flask 下，而不是 flask admin init-admin
cli_commands_bp = Blueprint("commands", __name__, cli_group=None)

# 將所有管理員相關指令添加到 Blueprint
cli_commands_bp.cli.add_command(init_admin_command)
cli_commands_bp.cli.add_command(list_admins_command)
cli_commands_bp.cli.add_command(reset_admin_password_command)

# 將所有評分相關指令添加到 Blueprint
cli_commands_bp.cli.add_command(recalculate_all_ratings_command)
cli_commands_bp.cli.add_command(reset_all_ratings_command)
cli_commands_bp.cli.add_command(rating_stats_command)
cli_commands_bp.cli.add_command(validate_ratings_command)
