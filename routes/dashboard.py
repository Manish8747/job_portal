from flask import Blueprint, current_app, request, jsonify, render_template, url_for, redirect, flash, session
from flask_jwt_extended import decode_token
from datetime import datetime
from .models import db, User, Job, Application
from werkzeug.utils import secure_filename
import os




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

    query = request.args.get('q', '').strip()

    if query:
        # Search jobs by title or poster's (company) name
        jobs = Job.query.join(User, Job.posted_by == User.id).filter(
            (Job.title.ilike(f"%{query}%")) |
            (User.name.ilike(f"%{query}%"))
        ).order_by(Job.id.desc()).all()
    else:
        jobs = Job.query.order_by(Job.id.desc()).all()

    return render_template('dashboard/seeker_dashboard.html', jobs=jobs)


@dashboard_bp.route('/seeker/profile', methods=['GET', 'POST'])
def seeker_profile():
    access_token = session.get('access_token')
    if not access_token or not is_token_valid(access_token):
        flash('You need to log in first', 'danger')
        return redirect(url_for('auth.login'))

    user_data = decode_token(access_token)
    user_id = user_data.get('sub')
    role = user_data.get('role')

    if role != 'Job Seeker':
        flash("Access denied.", "danger")
        return redirect(url_for('dashboard.employer_dashboard'))

    user = User.query.get(user_id)

    if request.method == 'POST':
        # Handle resume upload
        if 'resume' in request.files:
            resume_file = request.files['resume']
            if resume_file.filename != '':
                filename = secure_filename(resume_file.filename)
                # Save the file in a dedicated folder, e.g. 'uploads/resumes'
                upload_path = os.path.join(current_app.root_path, 'static/uploads/resumes', filename)
                resume_file.save(upload_path)
                # Update user resume path in DB
                user.resume = f'uploads/resumes/{filename}'
                db.session.commit()
                flash('Resume uploaded successfully.', 'success')
            else:
                flash('No file selected.', 'warning')

    # Get user's applied jobs with status
    applications = Application.query.filter_by(seeker_id=user_id).join(Job).add_columns(
        Job.title, Job.posted_by, Application.status
    ).all()


    # To get company names of posted jobs:
    applied_jobs = []
    for app, job_title, poster_id, status in applications:
        company = User.query.get(poster_id)
        applied_jobs.append({
            'job_title': job_title,
            'company_name': company.name if company else 'Unknown',
            'status': status
        })

    return render_template('dashboard/seeker_profile.html', user=user, applied_jobs=applied_jobs)
