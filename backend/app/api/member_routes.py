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
                "is_active": member.is_active,
                "notes": member.notes
            })
        return jsonify(member_data)
    except Exception as e:
        print(f"Error in get_all_members: {e}")  # 伺服器端日誌
        return jsonify({"error": "An error occurred while fetching members."}), 500


@bp.route('/members', methods=['POST'])
# @jwt_required() # 如果未來加入 JWT 認證，取消註解此行
def create_member():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request payload must be JSON"}), 400

    # 1. 提取資料
    name = data.get('name')
    student_id = data.get('student_id')
    gender_str = data.get('gender')  # 前端應傳送 Enum 的 NAME，例如 'MALE'
    position_str = data.get('position')  # 前端應傳送 Enum 的 NAME，例如 'SINGLES'
    is_active_val = data.get('is_active', True)  # 如果前端沒給，預設為 True
    notes = data.get('notes')

    # 2. 後端資料驗證
    errors = {}
    if not name:
        errors['name'] = "Name is required."
    elif len(name) > 100:
        errors['name'] = "Name cannot exceed 100 characters."

    if student_id:
        if len(student_id) > 20:
            errors['student_id'] = "Student ID cannot exceed 20 characters."
        if TeamMember.query.filter_by(student_id=student_id).first():
            errors['student_id'] = f"Student ID '{student_id}' already exists."

    gender_enum = GenderEnum.get_by_name(gender_str)  # 使用 classmethod 轉換
    if gender_str and gender_enum is None:  # 如果前端傳了值但無法轉換
        errors['gender'] = f"Invalid gender value: '{gender_str}'. Valid are: {[e.name for e in GenderEnum]}."

    position_enum = PositionEnum.get_by_name(position_str)  # 使用 classmethod 轉換
    if position_str and position_enum is None:
        errors[
            'position'] = f"Invalid position value: '{position_str}'. Valid are: {[e.name for e in PositionEnum]}."


    if not isinstance(is_active_val, bool):
        errors['is_active'] = "is_active must be a boolean (true or false)."

    if errors:
        return jsonify({"error": "Input validation failed", "details": errors}), 400

    # 3. 創建模型實例
    try:
        new_member = TeamMember(
            name=name,
            student_id=student_id,
            gender=gender_enum,
            position=position_enum,
            is_active=is_active_val,
            notes=notes
        )

        db.session.add(new_member)
        db.session.commit()

        return jsonify({
            "message": "Team member created successfully!",
            "member": new_member.to_dict()  # 使用 to_dict()
        }), 201

    except IntegrityError:  # 主要由 student_id unique 約束觸發
        db.session.rollback()
        return jsonify({"error": "Database integrity error. Student ID might already exist if it's unique."}), 409
    except Exception as e:
        db.session.rollback()
        print(f"Unexpected error creating member: {str(e)}")  # 伺服器日誌
        return jsonify({"error": "An unexpected error occurred on the server."}), 500