from flask import Blueprint

api_bp = Blueprint("api", __name__)


from . import (
    auth_routes,
    leaderboard_routes,
    match_routes,
    member_routes,
    organization_routes,
    profile_routes,
)
