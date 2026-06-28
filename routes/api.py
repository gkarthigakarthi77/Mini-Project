from flask import Blueprint, request, jsonify, send_file
from flask_login import login_required, current_user
from services import PasswordAnalyzer, PasswordGenerator
from services.password_history import PasswordHistoryService
from services.report_generator import ReportGenerator
from utils.logger import log_action
from datetime import datetime, timedelta
import logging
from models import PasswordHistory  # ✅ Import added
from extensions import csrf          # ✅ CSRF import

api_bp = Blueprint('api', __name__)
logger = logging.getLogger(__name__)

# ✅ Disable CSRF for all API routes (they use JSON)
@api_bp.before_request
def exempt_csrf():
    if request.method in ['POST', 'PUT', 'DELETE']:
        csrf.exempt(api_bp)


@api_bp.route('/analyze', methods=['POST'])
@login_required
def analyze():
    data = request.get_json()
    if not data or 'password' not in data:
        return jsonify({'error': 'Password is required'}), 400
    password = data['password']
    if not password or len(password) < 1:
        return jsonify({'error': 'Password cannot be empty'}), 400
    try:
        result = PasswordAnalyzer.analyze(password)
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        return jsonify({'error': 'Analysis failed'}), 500
    try:
        record = PasswordHistoryService.store_analysis(password, result)
        result['history_id'] = record.id
    except Exception as e:
        logger.error(f"History storage error: {e}")
    result.pop('password', None)
    result.pop('zxcvbn', None)
    return jsonify(result), 200


@api_bp.route('/generate', methods=['POST'])
@login_required
def generate():
    data = request.get_json() or {}
    length = data.get('length', 16)
    use_upper = data.get('use_upper', True)
    use_lower = data.get('use_lower', True)
    use_numbers = data.get('use_numbers', True)
    use_symbols = data.get('use_symbols', True)
    exclude_similar = data.get('exclude_similar', False)
    exclude_ambiguous = data.get('exclude_ambiguous', False)
    try:
        password = PasswordGenerator.generate(
            length=length,
            use_upper=use_upper,
            use_lower=use_lower,
            use_numbers=use_numbers,
            use_symbols=use_symbols,
            exclude_similar=exclude_similar,
            exclude_ambiguous=exclude_ambiguous
        )
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Generation error: {e}")
        return jsonify({'error': 'Generation failed'}), 500
    return jsonify({'password': password}), 200


@api_bp.route('/history', methods=['GET'])
@login_required
def history():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '').strip()
    try:
        paginated = PasswordHistoryService.get_user_history(
            user_id=current_user.id,
            search=search if search else None,
            page=page,
            per_page=per_page
        )
    except Exception as e:
        logger.error(f"History fetch error: {e}")
        return jsonify({'error': 'Failed to fetch history'}), 500
    items = [{
        'id': r.id,
        'hash_preview': r.password_hash[:8] + '...',
        'score': r.strength_score,
        'level': r.strength_level,
        'created_at': r.created_at.strftime('%Y-%m-%d %H:%M')
    } for r in paginated.items]
    return jsonify({
        'items': items,
        'total': paginated.total,
        'page': paginated.page,
        'per_page': paginated.per_page,
        'pages': paginated.pages
    }), 200


@api_bp.route('/history/<int:record_id>', methods=['DELETE'])
@login_required
def delete_history(record_id):
    try:
        success = PasswordHistoryService.delete_record(record_id, current_user.id)
        if success:
            log_action(f"Deleted history record {record_id}")
            return jsonify({'message': 'Deleted successfully'}), 200
        return jsonify({'error': 'Record not found'}), 404
    except Exception as e:
        logger.error(f"Delete error: {e}")
        return jsonify({'error': 'Delete failed'}), 500


@api_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard_stats():
    try:
        stats = PasswordHistoryService.get_stats(current_user.id)
        recent = PasswordHistoryService.get_recent(current_user.id, limit=5)
    except Exception as e:
        logger.error(f"Dashboard stats error: {e}")
        return jsonify({'error': 'Failed to fetch stats'}), 500
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=7)
    records = PasswordHistory.query.filter(
        PasswordHistory.user_id == current_user.id,
        PasswordHistory.created_at >= start_date
    ).all()
    daily_scores = {}
    for r in records:
        day = r.created_at.strftime('%Y-%m-%d')
        daily_scores.setdefault(day, []).append(r.strength_score)
    dates = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(8)]
    trend_data = []
    for d in dates:
        scores = daily_scores.get(d, [])
        avg = sum(scores) / len(scores) if scores else None
        trend_data.append(avg)
    dist = stats['distribution']
    return jsonify({
        'stats': stats,
        'recent': recent,
        'trend': {
            'labels': dates,
            'data': trend_data
        },
        'distribution': {
            'labels': list(dist.keys()),
            'data': list(dist.values())
        }
    }), 200


@api_bp.route('/report/<int:history_id>/download', methods=['GET'])
@login_required
def download_report(history_id):
    record = PasswordHistory.query.filter_by(id=history_id, user_id=current_user.id).first()
    if not record:
        return jsonify({'error': 'Record not found'}), 404
    analysis_data = {
        'strength_score': record.strength_score,
        'strength_level': record.strength_level,
        'entropy_bits': record.entropy,
        'estimated_crack_time_display': PasswordAnalyzer._format_crack_time(2 ** record.entropy / 1e10) if record.entropy else 'Unknown',
        'randomness': record.strength_score >= 40,
        'recommendations': []
    }
    if record.strength_score < 40:
        analysis_data['recommendations'] = ['Use a longer password.', 'Add more character types.']
    elif record.strength_score < 60:
        analysis_data['recommendations'] = ['Consider adding special characters.', 'Avoid common patterns.']
    else:
        analysis_data['recommendations'] = ['Your password is strong!', 'Keep using secure practices.']
    try:
        filename = ReportGenerator.generate_report(analysis_data, current_user.username, None)
        log_action(f"Generated report for history {history_id}")
        return send_file(filename, as_attachment=True, download_name=f'securepass_report_{history_id}.pdf')
    except Exception as e:
        logger.error(f"PDF generation error: {e}")
        return jsonify({'error': 'Failed to generate report'}), 500