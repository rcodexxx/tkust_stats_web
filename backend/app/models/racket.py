# backend/app/models/racket.py
from typing import Dict

from sqlalchemy import Integer, String
from sqlalchemy.orm import relationship

from ..extensions import db


class Racket(db.Model):
    __tablename__ = "rackets"

    id = db.Column(Integer, primary_key=True, comment="球拍唯一識別碼")
    brand = db.Column(String(50), nullable=False, index=True, comment="品牌")
    model_name = db.Column(String(100), nullable=False, index=True, comment="型號名稱")

    members_using = relationship("Member", back_populates="racket")

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "brand": self.brand,
            "model_name": self.model_name,
        }

    def __repr__(self) -> str:
        return f"<Racket id={self.id}, brand='{self.brand}', model='{self.model_name}'>"
