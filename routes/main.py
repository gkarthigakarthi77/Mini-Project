from flask import Blueprint, render_template
from flask_login import login_required

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    return render_template('main/index.html')


@main_bp.route('/analyzer')
@login_required
def analyzer():
    return render_template('main/analyzer.html')


@main_bp.route('/generator')
@login_required
def generator():
    return render_template('main/generator.html')


@main_bp.route('/history')
@login_required
def history():
    return render_template('main/history.html')


@main_bp.route('/learn')
def learn():
    return render_template('main/learn.html')