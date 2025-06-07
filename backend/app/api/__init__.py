from flask import Blueprint


api_bp = Blueprint("api", __name__)


from . import (
    match_routes,
    member_routes,
    auth_routes,
    profile_routes,
    organization_routes,
)
