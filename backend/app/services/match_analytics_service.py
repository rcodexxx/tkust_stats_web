# backend/app/services/match_analytics_service.py
from sqlalchemy import and_, or_

from ..models import Match, MatchRecord


class MatchAnalyticsService:
    @staticmethod
    def get_match_statistics(args: dict = None) -> dict:
        try:
            query = MatchRecord.query.join(Match)

            if args:
                if start_date := args.get("start_date"):
                    query = query.filter(Match.match_date >= start_date)
                if end_date := args.get("end_date"):
                    query = query.filter(Match.match_date <= end_date)
                if match_type := args.get("match_type"):
                    query = query.filter(Match.match_type == match_type)
                if match_format := args.get("match_format"):
                    query = query.filter(Match.match_format == match_format)

            total_matches = query.count()
            if total_matches == 0:
                return {
                    "total_matches": 0,
                    "total_games": 0,
                    "average_games_per_match": 0.0,
                    "match_type_distribution": {},
                    "match_format_distribution": {},
                }

            records = query.all()
            total_games = sum(record.a_games + record.b_games for record in records)
            average_games = round(total_games / total_matches, 2)

            match_type_dist = {}
            match_format_dist = {}

            for record in records:
                if record.match:
                    match_type = record.match.match_type.value
                    match_format = record.match.match_format.value
                    match_type_dist[match_type] = match_type_dist.get(match_type, 0) + 1
                    match_format_dist[match_format] = (
                        match_format_dist.get(match_format, 0) + 1
                    )

            return {
                "total_matches": total_matches,
                "total_games": total_games,
                "average_games_per_match": average_games,
                "match_type_distribution": match_type_dist,
                "match_format_distribution": match_format_dist,
            }

        except Exception as e:
            raise Exception(f"獲取比賽統計時發生錯誤: {e}")

    @staticmethod
    def analyze_member_serve_performance(member_id: int, limit: int = 10) -> dict:
        matches = (
            MatchRecord.query.filter(
                and_(
                    or_(
                        MatchRecord.player1_id == member_id,
                        MatchRecord.player2_id == member_id,
                        MatchRecord.player3_id == member_id,
                        MatchRecord.player4_id == member_id,
                    ),
                    MatchRecord.first_serve_side.isnot(None),
                )
            )
            .order_by(MatchRecord.id.desc())
            .limit(limit)
            .all()
        )

        if not matches:
            return {
                "member_id": member_id,
                "matches_analyzed": 0,
                "has_data": False,
                "message": "該球員沒有發球記錄的比賽",
            }

        total_serve_games = 0
        total_serve_wins = 0
        serve_side_distribution = {"side_a": 0, "side_b": 0}
        match_details = []

        for match in matches:
            player_side = None
            if member_id in [match.player1_id, match.player2_id]:
                player_side = "side_a"
            elif member_id in [match.player3_id, match.player4_id]:
                player_side = "side_b"

            if not player_side:
                continue

            match_serve_games = 0
            match_serve_wins = 0
            games_detail = match.get_all_games_scores()

            for game_detail in games_detail:
                game_num = game_detail["game"]
                serve_side = match.get_serve_side_for_game(game_num)

                if serve_side == player_side:
                    total_serve_games += 1
                    match_serve_games += 1
                    serve_side_distribution[player_side] += 1

                    if game_detail["winner"] == (
                        "A" if player_side == "side_a" else "B"
                    ):
                        total_serve_wins += 1
                        match_serve_wins += 1

            match_serve_win_rate = (
                (match_serve_wins / match_serve_games * 100)
                if match_serve_games > 0
                else 0.0
            )

            match_details.append(
                {
                    "match_id": match.id,
                    "match_date": match.match.match_date.isoformat()
                    if match.match
                    else None,
                    "player_side": player_side,
                    "serve_games": match_serve_games,
                    "serve_wins": match_serve_wins,
                    "serve_win_rate": round(match_serve_win_rate, 1),
                }
            )

        overall_serve_win_rate = (
            (total_serve_wins / total_serve_games * 100)
            if total_serve_games > 0
            else 0.0
        )

        return {
            "member_id": member_id,
            "matches_analyzed": len(matches),
            "has_data": True,
            "overall_stats": {
                "total_serve_games": total_serve_games,
                "total_serve_wins": total_serve_wins,
                "serve_win_rate": round(overall_serve_win_rate, 1),
                "serve_side_distribution": serve_side_distribution,
                "performance_level": MatchAnalyticsService._get_performance_level(
                    overall_serve_win_rate
                ),
            },
            "recent_matches": match_details,
        }

    @staticmethod
    def get_match_serve_analysis(record_id: int) -> dict:
        record = MatchRecord.query.get(record_id)
        if not record:
            raise Exception("找不到指定的比賽記錄")

        if not record.first_serve_side:
            return {
                "match_record_id": record_id,
                "has_serve_tracking": False,
                "message": "該比賽記錄沒有發球記錄",
            }

        serve_details = record.get_all_games_scores_with_serve()
        serve_advantage = record._calculate_serve_advantage()

        games_with_scores = [d for d in serve_details if d.get("has_score", False)]
        side_a_serves = sum(1 for d in games_with_scores if d["serve_side"] == "side_a")
        side_b_serves = sum(1 for d in games_with_scores if d["serve_side"] == "side_b")

        return {
            "match_record_id": record_id,
            "has_serve_tracking": True,
            "first_serve_side": record.first_serve_side.value,
            "serve_details": serve_details,
            "serve_advantage": serve_advantage,
            "summary": {
                "total_games_with_serve_record": len(games_with_scores),
                "side_a_serve_games": side_a_serves,
                "side_b_serve_games": side_b_serves,
                "side_a_serve_win_rate": serve_advantage["side_a"]["serve_win_rate"]
                if serve_advantage
                else 0,
                "side_b_serve_win_rate": serve_advantage["side_b"]["serve_win_rate"]
                if serve_advantage
                else 0,
            },
        }

    @staticmethod
    def get_recent_matches_summary(limit: int = 10) -> dict:
        matches = (
            MatchRecord.query.join(Match)
            .order_by(Match.match_date.desc())
            .limit(limit)
            .all()
        )

        match_summaries = []
        for match in matches:
            match_summaries.append(
                {
                    "id": match.id,
                    "match_date": match.match.match_date.isoformat()
                    if match.match
                    else None,
                    "match_type": match.match.match_type.value if match.match else None,
                    "a_games": match.a_games,
                    "b_games": match.b_games,
                    "total_games": match.a_games + match.b_games,
                    "has_detailed_scores": match.has_detailed_scores(),
                    "has_serve_tracking": bool(match.first_serve_side),
                }
            )

        return {"total": len(match_summaries), "matches": match_summaries}

    @staticmethod
    def _get_performance_level(win_rate: float) -> str:
        if win_rate >= 70:
            return "優秀"
        elif win_rate >= 60:
            return "良好"
        elif win_rate >= 50:
            return "普通"
        else:
            return "需改善"
