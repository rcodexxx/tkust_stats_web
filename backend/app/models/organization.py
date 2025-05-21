# app/models/organization.py
from ..extensions import db

class Organization(db.Model):
    __tablename__ = 'organizations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False, comment="組織/隊伍全名")
    # short_name = db.Column(db.String(50), unique=True, nullable=True, comment="簡稱")
    # notes = db.Column(db.Text, nullable=True, comment="備註")

    # 反向關聯: 一個組織可以有多個 TeamMember
    # 'members' 屬性可以讓您從 Organization 實例訪問其所有成員
    # members = db.relationship('TeamMember', back_populates='organization_id', lazy='dynamic')
    # 如果 TeamMember 中關聯名為 'organization_info'，則這裡 backref='organization_info'

    def __repr__(self):
        return f"<Organization {self.name}>"