from extensions import db
from datetime import datetime


class PasswordHistory(db.Model):
    __tablename__ = 'password_history'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    strength_score = db.Column(db.Integer)
    entropy = db.Column(db.Float)
    strength_level = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.Index('idx_user_id', 'user_id'),
        db.Index('idx_created_at', 'created_at'),
    )

    def __repr__(self):
        return f'<PasswordHistory user_id={self.user_id} score={self.strength_score}>'