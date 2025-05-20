from flask import Blueprint

bp = Blueprint('api', __name__)

from . import routes # 或者 from . import leaderboard, match_routes 等 (如果拆分檔案)