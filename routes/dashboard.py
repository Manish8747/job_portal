from flask import Blueprint, request, jsonify, render_template, url_for, redirect, flash, session
from flask_jwt_extended import decode_token
from datetime import datetime


dashboard_bp = Blueprint('dashboard', __name__, template_folder='templates')


# Function to check if the token is valid
def is_token_valid(token):
    try:
        decoded_token = decode_token(token)
        exp_timestamp = decoded_token['exp']
        now_timestamp = int(datetime.now().timestamp())
        return now_timestamp < exp_timestamp
    except Exception:
        return False

#Function for employer's dashboard
@dashboard_bp.route('/employer_dashboard')
def employer_dashboard():
    access_token = session.get('access_token')
    if not access_token or is_token_valid(access_token):
        flash('You need to log in first', 'danger')
        return redirect(url_for('auth.login'))

    return render_template('dashboard/employer_dashboard.html')

#Function for seeker's dashboard
@dashboard_bp.route('/seeker_dashboard')
def seeker_dashboard():
    access_token = session.get('access_token')
    if not access_token or is_token_valid(access_token):
        flash('You need to log in first', 'danger')
        return redirect(url_for('auth.login'))

    return render_template('dashboard/seeker_dashboard.html')