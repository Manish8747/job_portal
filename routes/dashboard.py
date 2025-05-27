from flask import Blueprint, request, jsonify, render_template, url_for, redirect, flash, session
from flask_jwt_extended import decode_token
from datetime import datetime
from .models import db, User, Job
dashboard_bp = Blueprint('dashboard', __name__, template_folder='templates')


# Function to check if the token is valid
def is_token_valid(token):
    try:
        decoded_token = decode_token(token)
        exp_timestamp = decoded_token['exp']
        now_timestamp = int(datetime.now().timestamp())
        return now_timestamp < exp_timestamp
    except Exception as e:
        print("[TOKEN VALIDATION ERROR]", e)
        return False

#Function for employer's dashboard
@dashboard_bp.route('/employer_dashboard')
def employer_dashboard():
    access_token = session.get('access_token')
    if not access_token or not is_token_valid(access_token):
        flash('You need to log in first', 'danger')
        return redirect(url_for('auth.login'))

    return render_template('dashboard/employer_dashboard.html')

#Function for seeker's dashboard
@dashboard_bp.route('/seeker_dashboard')
def seeker_dashboard():
    access_token = session.get('access_token')
    if not access_token or not is_token_valid(access_token):
        flash('You need to log in first', 'danger')
        return redirect(url_for('auth.login'))

    user = decode_token(access_token)
    user_id = user.get('sub')
    role = user.get('role')
    db_user = User.query.get(user_id)

    if role != 'Job Seeker':
        flash("Access denied.", "danger")
        return redirect(url_for('dashboard.employer_dashboard'))

    jobs = Job.query.order_by(Job.id.desc()).all()
    return render_template('dashboard/seeker_dashboard.html', jobs=jobs)
