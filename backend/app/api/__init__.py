from flask import Blueprint

bp = Blueprint("api", __name__)

from . import leaderboard_routes, match_routes, member_routes
