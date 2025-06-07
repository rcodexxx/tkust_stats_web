# backend/app/schemas/match_schemas.py
from marshmallow import Schema, fields, validate, validates_schema, ValidationError
from marshmallow_enum import EnumField

# 假設您的 enums 和 models 在這些路徑
from ..models import Member
from ..models.enums.match_enums import MatchTypeEnum, MatchFormatEnum


# --- 用於巢狀顯示的簡潔 Schema ---
class SimpleMemberSchema(Schema):
    """僅序列化隊員的基礎資訊，用於比賽記錄的回應中。"""

    id = fields.Int(dump_only=True)
    name = fields.Str(dump_only=True)
    # 顯示名稱優先使用 User model 上的 display_name，若無則用 Member 的 name
    display_name = fields.Method("get_display_name_from_user", dump_only=True)

    def get_display_name_from_user(self, obj):
        if obj and obj.user and obj.user.display_name:
            return obj.user.display_name
        elif obj and obj.name:
            return obj.name
        return None


# --- 創建比賽記錄的請求 Schema ---
class MatchRecordCreateSchema(Schema):
    match_date = fields.Date(required=True)
    # 註：根據您的模型，您模型中的 match_type 和 match_format Enum 可能與欄位名語義相反。
    # 此 Schema 採用了更符合語義的對應關係，確保 API 的清晰性。
    match_type = EnumField(MatchTypeEnum, by_value=True, required=True, error="無效的比賽類型。")
    match_format = EnumField(MatchFormatEnum, by_value=True, required=True, error="無效的賽制。")

    # 更新為 player1_id, player2_id, player3_id, player4_id
    player1_id = fields.Int(required=True)
    player2_id = fields.Int(required=False, allow_none=True)  # 雙打時的隊友
    player3_id = fields.Int(required=True)
    player4_id = fields.Int(required=False, allow_none=True)  # 雙打時的隊友

    # 更新為 a_games, b_games
    a_games = fields.Int(required=True, validate=validate.Range(min=0), metadata={"description": "A方贏得的局數"})
    b_games = fields.Int(required=True, validate=validate.Range(min=0), metadata={"description": "B方贏得的局數"})

    match_notes = fields.Str(required=False, allow_none=True)

    @validates_schema
    def validate_players_and_score(self, data, **kwargs):
        """對球員和分數進行綜合驗證。"""
        # 驗證球員不重複
        player_ids = [data.get("player1_id"), data.get("player2_id"), data.get("player3_id"), data.get("player4_id")]
        valid_ids = {pid for pid in player_ids if pid is not None}
        if len(valid_ids) < len([pid for pid in player_ids if pid is not None]):
            raise ValidationError("一場比賽中不能有重複的球員。", field_name="_schema")

        # 驗證所有傳入的球員 ID 都是有效的 Member
        found_members_count = Member.query.filter(Member.id.in_(valid_ids)).count()
        if found_members_count != len(valid_ids):
            raise ValidationError("提供了無效的球員 ID。", field_name="_schema")

        # 驗證分數不能相同（不支援平局）
        if data.get("a_games") == data.get("b_games"):
            raise ValidationError("比賽局數不能相同（不支援平局）。", field_name="a_games")


# --- 顯示比賽記錄的回應 Schema ---
class MatchRecordResponseSchema(Schema):
    id = fields.Int(dump_only=True)
    match_date = fields.Date(dump_only=True)
    match_type = EnumField(MatchTypeEnum, by_value=True, dump_only=True)
    match_format = EnumField(MatchFormatEnum, by_value=True, dump_only=True)

    # 更新 player 欄位以匹配模型，並使用我們定義的 SimpleMemberSchema
    player1 = fields.Nested(SimpleMemberSchema, dump_only=True)
    player2 = fields.Nested(SimpleMemberSchema, dump_only=True, allow_none=True)
    player3 = fields.Nested(SimpleMemberSchema, dump_only=True)
    player4 = fields.Nested(SimpleMemberSchema, dump_only=True, allow_none=True)

    # 更新 score 欄位以匹配模型
    a_games = fields.Int(dump_only=True)
    b_games = fields.Int(dump_only=True)
    side_a_outcome = fields.Str(attribute="side_a_outcome.value", dump_only=True)

    match_notes = fields.Str(dump_only=True, allow_none=True)

    class Meta:
        ordered = True
