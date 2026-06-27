from extensions import db
from models import Log
from flask_login import current_user
from flask import request
import logging

logger = logging.getLogger(__name__)

def log_action(action: str, details: str = None):
    try:
        log = Log(
            user_id=current_user.id if current_user.is_authenticated else None,
            action=action,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            details=details
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        logger.error(f"Failed to log action: {e}")