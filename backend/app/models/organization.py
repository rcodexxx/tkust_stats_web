# backend/app/models/organization.py

from ..extensions import db


class Organization(db.Model):
    __tablename__ = "organizations"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(
        db.String(100), unique=True, nullable=False, index=True, comment="組織/隊伍"
    )
    city = db.Column(db.String(50), nullable=True, comment="所在城市")
    notes = db.Column(db.Text, nullable=True, comment="備註")

    # 反向關聯: 一個 Organization 可以有多個 Member (TeamMember)
    # 'members' 屬性可以讓您從 Organization 實例訪問其所有成員
    members = db.relationship(
        "Member", back_populates="organization_profile", lazy="dynamic"
    )  # 假設您的成員模型類名是 Member

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "city": self.city,
            "notes": self.notes,
            "member_count": self.members.count(),  # (可選) 回傳成員數量
        }

    def __repr__(self):
        return f"<Organization {self.name}>"
