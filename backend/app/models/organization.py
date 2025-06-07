# backend/app/models/organization.py
from typing import Dict

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import relationship

from ..extensions import db


class Organization(db.Model):
    __tablename__ = "organizations"

    id = db.Column(Integer, primary_key=True, comment="組織唯一識別碼")
    name = db.Column(String(100), unique=True, nullable=False, index=True, comment="組織全名")
    short_name = db.Column(String(30), unique=True, nullable=True, index=True, comment="組織簡稱或代號")
    description = db.Column(Text, nullable=True, comment="組織描述")

    contact_person = db.Column(String(50), nullable=True, comment="主要聯絡人")
    contact_email = db.Column(String(120), nullable=True, comment="聯絡Email")
    contact_phone = db.Column(String(30), nullable=True, comment="聯絡電話")

    members = relationship("Member", back_populates="organization")

    def to_dict(self, members_count: bool = False, contact_info: bool = False) -> Dict:
        data = {
            "id": self.id,
            "name": self.name,
            "short_name": self.short_name,
            "description": self.description,
        }
        if members_count:
            data["contact_person"] = self.contact_person
            data["contact_email"] = self.contact_email
            data["contact_phone"] = self.contact_phone

        if members_count:
            data["members_count"] = len(self.members) if self.members else 0
        return data

    def __repr__(self):
        return f"<Organization {self.name}>"
