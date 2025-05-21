# app/models/racket.py
from ..extensions import db

class Racket(db.Model):
    __tablename__ = 'rackets'
    id = db.Column(db.Integer, primary_key=True)
    # brand = db.Column(db.String(50), nullable=False, comment="品牌")
    # model_name = db.Column(db.String(100), nullable=False, comment="型號名稱")
    # year = db.Column(db.Integer, nullable=True, comment="年份")
    # notes = db.Column(db.Text, nullable=True, comment="備註/規格")

    # 反向關聯: 一個球拍型號可以被多個 TeamMember 使用
    # 'users' 屬性可以讓您從 Racket 實例訪問所有使用此球拍的成員
    # users = db.relationship('TeamMember', back_populates='racket_info', lazy='dynamic')
    # # 如果 TeamMember 中關聯名為 'racket_details'，則這裡 backref='racket_details'
    #
    # # 確保品牌和型號的組合是唯一的，避免重複球拍定義 (可選)
    # __table_args__ = (db.UniqueConstraint('brand', 'model_name', name='_brand_model_uc'),)

    def __repr__(self):
        return f"<Racket {self.brand} {self.model_name}>"