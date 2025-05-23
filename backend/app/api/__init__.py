from flask import Blueprint

bp = Blueprint('api', __name__)

from . import member_routes
from . import leaderboard_routes
from . import match_routes