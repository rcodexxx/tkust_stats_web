from flask import request, jsonify
from . import bp
from ..extensions import db
from ..models.team_member import TeamMember
from ..models.enums import GenderEnum, PositionEnum
from sqlalchemy.exc import IntegrityError
import datetime


@bp.route('/members', methods=['GET'])  # 通常用 /members 獲取所有成員列表
def get_all_members():
    """獲取所有活躍球員列表，主要用於表單選擇等，按姓名排序"""
    try:
        # active_only_str = request.args.get('active_only', 'true', type=str)  # 獲取查詢參數
        # active_only = active_only_str.lower() == 'true'
        #
        query = TeamMember.query
        # if active_only:
        #     query = query.filter_by(is_active=True)

        members = query.order_by(TeamMember.name).all()

        member_data = []
        for member in members:
            member_data.append({
                "id": member.id,
                "name": member.name,
                "score": member.score,
                "student_id": member.student_id,
                "gender": member.gender.value if member.gender else None,  # Enum 的 .value 會回傳設定的值
                "position": member.position.value if member.position else None,
                "join_date": member.join_date.isoformat() if member.join_date else None,
                "leave_date": member.leave_date.isoformat() if member.leave_date else None,
                "is_active": member.is_active,
                "notes": member.notes
            })
        return jsonify(member_data)
    except Exception as e:
        print(f"Error in get_all_members: {e}")  # 伺服器端日誌
        return jsonify({"error": "An error occurred while fetching members."}), 500


@bp.route('/members', methods=['POST'])
def create_member():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request payload must be JSON"}), 400

    # 1. 提取資料 (並提供預設值或處理缺失的可選欄位)
    name = data.get('name')
    student_id = data.get('student_id')
    # organization_id = data.get('organization_id')  # 假設類型
    gender_str = data.get('gender')  # 前端傳送 Enum 的 NAME (大寫)
    position_str = data.get('position')  # 前端傳送 Enum 的 NAME (大寫)
    join_date_str = data.get('join_date')  # 預期格式 'YYYY-MM-DD'
    leave_date_str = data.get('leave_date')  # 預期格式 'YYYY-MM-DD'
    is_active_val = data.get('is_active', True)  # 如果沒提供，預設為 True
    # racket = data.get('racket')
    notes = data.get('notes')
    score = 0  # 如果沒提供，預設為 0

    # 2. 後端資料驗證 (非常重要)
    errors = {}
    if not name:
        errors['name'] = "Name is required."
    elif len(name) > 50:  # 假設模型中 name 欄位長度限制為 100
        errors['name'] = "Name is too long (max 100 characters)."

    if student_id and len(student_id) > 20:  # 假設學號長度限制
        errors['student_id'] = "Student ID is too long (max 20 characters)."

    # 檢查 student_id 是否已存在 (如果它是唯一的)
    if student_id and TeamMember.query.filter_by(student_id=student_id).first():
        errors['student_id'] = f"Student ID '{student_id}' already exists."

    gender_enum = None
    if gender_str:
        try:
            gender_enum = GenderEnum[gender_str.upper()]
        except KeyError:
            errors['gender'] = f"Invalid gender value: '{gender_str}'. Valid values are: {[e.name for e in GenderEnum]}."

    position_enum = None
    if position_str:
        try:
            position_enum = PositionEnum[position_str.upper()]
        except KeyError:
            errors['position'] = f"Invalid position value: '{position_str}'. Valid values are: {[e.name for e in PositionEnum]}."

    join_date_obj = None
    if join_date_str:
        try:
            join_date_obj = datetime.datetime.strptime(join_date_str, '%Y-%m-%d').date()
        except ValueError:
            errors['join_date'] = "Invalid join_date format. Expected YYYY-MM-DD."
    else:  # 如果前端沒傳，預設為今天
        join_date_obj = datetime.date.today()

    leave_date_obj = None
    if leave_date_str:
        try:
            leave_date_obj = datetime.datetime.strptime(leave_date_str, '%Y-%m-%d').date()
        except ValueError:
            errors['leave_date'] = "Invalid leave_date format. Expected YYYY-MM-DD."

    if not isinstance(is_active_val, bool):
        errors['is_active'] = "is_active must be a boolean (true or false)."

    if racket and len(racket) > 100:  # 假設球拍長度限制
        errors['racket'] = "Racket information is too long (max 100 characters)."

    if errors:
        return jsonify({"error": "Input validation failed", "details": errors}), 400  # 400 Bad Request

    # 3. 創建模型實例
    try:
        new_member = TeamMember(
            name=name,
            student_id=student_id if student_id else None,
            organization_id=organization_id,  # 假設 organization_id 允許為 None
            gender=gender_enum,
            position=position_enum,  # 注意：您的 get_members 用的是 position，之前模型用的是 preferred_position，請統一
            score=score,
            racket=racket if racket else None,
            join_date=join_date_obj,
            leave_date=leave_date_obj,
            is_active=is_active_val,
            notes=notes
        )

        # 4. 加入資料庫並提交
        db.session.add(new_member)
        db.session.commit()

        # 5. 回傳成功訊息和新資源的數據 (與您的 get_members 格式盡量一致)
        return jsonify({
            "message": "Team member created successfully",
            "member": {
                "id": new_member.id,
                "name": new_member.name,
                "score": new_member.score,
                "student_id": new_member.student_id,
                "organization_id": new_member.organization_id,
                "gender": new_member.gender.value if new_member.gender else None,
                "position": new_member.position.value if new_member.position else None,
                "join_date": new_member.join_date.isoformat() if new_member.join_date else None,
                "leave_date": new_member.leave_date.isoformat() if new_member.leave_date else None,
                "is_active": new_member.is_active,
                "racket": new_member.racket
            }
        }), 201  # 201 Created 狀態碼

    except IntegrityError as e:  # 例如違反 unique 約束 (可能是 student_id 重複，如果資料庫層面有設定)
        db.session.rollback()
        if "unique constraint" in str(e.orig).lower():  # 嘗試從錯誤訊息判斷
            return jsonify({"error": "A unique field (like student_id) likely already exists."}), 409  # 409 Conflict
        return jsonify({"error": "Database integrity error."}), 409
    except Exception as e:
        db.session.rollback()
        print(f"Error creating member: {e}")  # 伺服器端日誌，除錯用
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500