from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from extensions import db
from models import User, PasswordHistory, Log
from utils.decorators import admin_required
from utils.logger import log_action
from datetime import datetime, timedelta
import logging

admin_bp = Blueprint('admin', __name__)
logger = logging.getLogger(__name__)


@admin_bp.route('/')
@login_required
@admin_required
def admin_panel():
    total_users = User.query.count()
    total_passwords = PasswordHistory.query.count()
    total_logs = Log.query.count()
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_logs = Log.query.order_by(Log.timestamp.desc()).limit(10).all()
    return render_template('admin/dashboard.html',
                           total_users=total_users,
                           total_passwords=total_passwords,
                           total_logs=total_logs,
                           recent_users=recent_users,
                           recent_logs=recent_logs)


@admin_bp.route('/users')
@login_required
@admin_required
def user_management():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    query = User.query
    if search:
        query = query.filter(db.or_(
            User.username.ilike(f'%{search}%'),
            User.email.ilike(f'%{search}%')
        ))
    paginated = query.order_by(User.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/users.html', users=paginated.items, pagination=paginated, search=search)


@admin_bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_user_active(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        return jsonify({'error': 'Cannot deactivate yourself'}), 400
    user.is_active = not user.is_active
    db.session.commit()
    log_action(f"Toggled user {user.username} active status to {user.is_active}")
    return jsonify({'message': 'User status updated', 'active': user.is_active}), 200


@admin_bp.route('/users/<int:user_id>/delete', methods=['DELETE'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        return jsonify({'error': 'Cannot delete yourself'}), 400
    PasswordHistory.query.filter_by(user_id=user.id).delete()
    Log.query.filter_by(user_id=user.id).delete()
    db.session.delete(user)
    db.session.commit()
    log_action(f"Deleted user {user.username} (ID {user.id})")
    return jsonify({'message': 'User deleted'}), 200


@admin_bp.route('/logs')
@login_required
@admin_required
def view_logs():
    page = request.args.get('page', 1, type=int)
    action_filter = request.args.get('action', '').strip()
    user_filter = request.args.get('user', '').strip()
    query = Log.query
    if action_filter:
        query = query.filter(Log.action.ilike(f'%{action_filter}%'))
    if user_filter:
        if user_filter.isdigit():
            query = query.filter(Log.user_id == int(user_filter))
        else:
            query = query.join(User).filter(User.username.ilike(f'%{user_filter}%'))
    paginated = query.order_by(Log.timestamp.desc()).paginate(page=page, per_page=30, error_out=False)
    return render_template('admin/logs.html', logs=paginated.items, pagination=paginated,
                           action_filter=action_filter, user_filter=user_filter)


@admin_bp.route('/logs/clear', methods=['POST'])
@login_required
@admin_required
def clear_logs():
    cutoff = datetime.utcnow() - timedelta(days=30)
    deleted = Log.query.filter(Log.timestamp < cutoff).delete()
    db.session.commit()
    log_action(f"Cleared {deleted} logs older than 30 days")
    return jsonify({'message': f'Cleared {deleted} logs'}), 200


@admin_bp.route('/stats')
@login_required
@admin_required
def stats_data():
    end = datetime.utcnow()
    start = end - timedelta(days=30)
    days = [(start + timedelta(days=i)).date() for i in range(31)]
    user_counts = []
    for d in days:
        count = User.query.filter(db.func.date(User.created_at) <= d).count()
        user_counts.append(count)
    daily_passwords = []
    for d in days:
        cnt = PasswordHistory.query.filter(db.func.date(PasswordHistory.created_at) == d).count()
        daily_passwords.append(cnt)
    return jsonify({
        'user_growth': {'labels': [d.strftime('%Y-%m-%d') for d in days], 'data': user_counts},
        'daily_passwords': {'labels': [d.strftime('%Y-%m-%d') for d in days], 'data': daily_passwords}
    }), 200


@admin_bp.route('/delete-all-passwords', methods=['POST'])
@login_required
@admin_required
def delete_all_passwords():
    count = PasswordHistory.query.delete()
    db.session.commit()
    log_action(f"Admin deleted all password history ({count} records)")
    return jsonify({'message': f'Deleted {count} records'}), 200