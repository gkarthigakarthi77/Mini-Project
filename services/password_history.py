import hashlib
from datetime import datetime
from extensions import db
from models import PasswordHistory
from flask_login import current_user
from utils.logger import log_action


class PasswordHistoryService:

    @staticmethod
    def store_analysis(password: str, analysis_result: dict) -> PasswordHistory:
        password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
        record = PasswordHistory(
            user_id=current_user.id,
            password_hash=password_hash,
            strength_score=analysis_result['strength_score'],
            entropy=analysis_result['entropy_bits'],
            strength_level=analysis_result['strength_level'],
            created_at=datetime.utcnow()
        )
        db.session.add(record)
        db.session.commit()
        log_action('Password analyzed', f'Score: {analysis_result["strength_score"]}, Level: {analysis_result["strength_level"]}')
        return record

    @staticmethod
    def get_user_history(user_id: int, search: str = None, page: int = 1, per_page: int = 10):
        query = PasswordHistory.query.filter_by(user_id=user_id)
        if search:
            if search.isdigit():
                query = query.filter(PasswordHistory.strength_score == int(search))
            else:
                query = query.filter(PasswordHistory.password_hash.startswith(search))
        query = query.order_by(PasswordHistory.created_at.desc())
        return query.paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def delete_record(record_id: int, user_id: int) -> bool:
        record = PasswordHistory.query.filter_by(id=record_id, user_id=user_id).first()
        if record:
            db.session.delete(record)
            db.session.commit()
            return True
        return False

    @staticmethod
    def get_stats(user_id: int) -> dict:
        records = PasswordHistory.query.filter_by(user_id=user_id).all()
        total = len(records)
        if total == 0:
            return {
                'total': 0,
                'average_score': 0,
                'strong_count': 0,
                'weak_count': 0,
                'distribution': {'Very Weak': 0, 'Weak': 0, 'Moderate': 0, 'Strong': 0, 'Very Strong': 0}
            }
        scores = [r.strength_score for r in records]
        avg_score = sum(scores) / total
        strong = sum(1 for r in records if r.strength_score >= 60)
        weak = sum(1 for r in records if r.strength_score < 40)
        levels = ['Very Weak', 'Weak', 'Moderate', 'Strong', 'Very Strong']
        dist = {level: 0 for level in levels}
        for r in records:
            dist[r.strength_level] = dist.get(r.strength_level, 0) + 1
        return {
            'total': total,
            'average_score': round(avg_score, 1),
            'strong_count': strong,
            'weak_count': weak,
            'distribution': dist
        }

    @staticmethod
    def get_recent(user_id: int, limit: int = 5) -> list:
        records = PasswordHistory.query.filter_by(user_id=user_id) \
            .order_by(PasswordHistory.created_at.desc()) \
            .limit(limit).all()
        return [{
            'id': r.id,
            'hash_preview': r.password_hash[:8] + '...',
            'score': r.strength_score,
            'level': r.strength_level,
            'created_at': r.created_at.strftime('%Y-%m-%d %H:%M')
        } for r in records]