import datetime

from ..extensions import db
from ..models.enums import GenderEnum, PositionEnum, UserRoleEnum
from ..models.member import Member
from ..models.user import User


def create_member(
    username: str,
    name: str,
    password: str = None,
    email: str = None,
    role: UserRoleEnum = UserRoleEnum.MEMBER,
    display_name: str = None,
    student_id: str = None,
    organization: str = None,
    gender: GenderEnum = None,
    position: PositionEnum = None,
    mu: float = None,
    sigma: float = None,
    join_date: datetime.date = None,
    is_active: bool = True,
    notes: str = None,
):
    """
    核心服務函數：創建 User 和關聯的 TeamMember。
    - username: 必須提供，用於 User 登入。
    - name: 必須提供，作為 TeamMember 的真實姓名。
    - password: 預設等於username
    - 其他 TeamMember 欄位可選，將使用提供的值或模型預設值。
    成功則返回 (new_user, new_member, actual_password_used)
    失敗則拋出 ValueError 或其他異常。
    """

    if User.query.filter_by(username=username).first():
        raise ValueError(f"使用者名稱 '{username}' 已存在。")

    new_user = User(
        username=username,
        email=email,
        role=role,
        is_active=is_active,
    )
    actual_password_used = password if password is not None else username
    new_user.set_password(actual_password_used)

    # 創建 TeamMember
    processed_student_id = student_id if student_id and student_id.strip() else None
    if (
        processed_student_id
        and Member.query.filter_by(student_id=processed_student_id).first()
    ):
        raise ValueError(f"學號 '{processed_student_id}' 已被其他成員使用。")

    final_display_name = display_name if display_name and display_name.strip() else name

    default_mu = Member.mu.default.arg if Member.mu.default else 25.0
    default_sigma = (
        Member.sigma.default.arg
        if Member.sigma.default
        else round(25.0 / 3.0, 4)
    )
    default_join_date = (
        Member.join_date.default.arg
        if Member.join_date.default
        else datetime.date.today()
    )

    new_member = Member(
        name=name,
        display_name=final_display_name,
        student_id=processed_student_id,
        organization=organization,
        gender=gender,
        position=position,
        mu=mu if mu is not None else default_mu,
        sigma=sigma if sigma is not None else default_sigma,
        join_date=join_date or default_join_date,
        is_active_member=(is_active if is_active is not None else False),
        notes=notes,
        user_account=new_user,
    )

    db.session.add(new_member)

    return new_user, new_member, actual_password_used
