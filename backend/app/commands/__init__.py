# backend/app/commands/__init__.py
from flask import Blueprint

from .init_admin import init_admin_command

# 創建一個 Blueprint 來組織命令
# cli_group=None 表示指令直接在 flask 下，而不是 flask seed init-admin
# 如果設為 'seed'，則指令會是 flask seed init-admin
cli_commands_bp = Blueprint("commands", __name__, cli_group=None)

# 將指令添加到 Blueprint
cli_commands_bp.cli.add_command(init_admin_command)
