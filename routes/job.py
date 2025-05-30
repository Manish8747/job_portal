from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort
from flask_jwt_extended import decode_token
from .models import db, User, Job, Application
import os
from werkzeug.utils import secure_filename
from sqlalchemy import func
from datetime import datetime
from flask_mail import Message
from routes.email import send_application_confirmation_email, send_status_update_email


job_bp = Blueprint('job', __name__, template_folder='templates')

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to decode the current user from JWT
def get_current_user():
    token = session.get('access_token')

    if token:
        try:
            decoded = decode_token(token)
            user_id = decoded.get('sub')
            user_role = decoded.get('role')
            user = User.query.get(user_id)

            if user and user.role == user_role:
                return user
        except Exception as e:
            print("[TOKEN ERROR]", e)
    return None


# Employer post new job
@job_bp.route('/post-job', methods=['GET', 'POST'])
def post_job():
    user = get_current_user()
    
    if not user:
        flash("You must be logged in to post a job.", "danger")
        return redirect(url_for('auth.login'))

    if user.role != 'Employer':
        flash("Access denied. Only Employers can post jobs.", "danger")
        return redirect(url_for('dashboard.seeker_dashboard'))

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        location = request.form.get('location')
        job_type = request.form.get('job_type')
        salary = request.form.get('salary')

        if not title or not description or not location or not job_type or not salary:
            flash("All fields are required.", "warning")
            return render_template('jobs/post_job.html')

        try:
            salary = float(salary)
        except ValueError:
            flash("Salary must be a number.", "warning")
            return render_template('jobs/post_job.html')

        new_job = Job(
            title=title,
            description=description,
            location=location,
            job_type=job_type,
            salary=salary,
            posted_by=user.id
        )
        db.session.add(new_job)
        db.session.commit()

        flash("Job posted successfully!", "success")
        return redirect(url_for('dashboard.employer_dashboard'))

    return render_template('jobs/post_job.html')

# Show My Posted Jobs with Applicant Counts
@job_bp.route('/my-posted-jobs')
def my_posted_jobs():
    user = get_current_user()
    if not user:
        flash("You must be logged in to view your posted jobs.", "danger")
        return redirect(url_for('auth.login'))

    if user.role != 'Employer':
        flash("Access denied.", "danger")
        return redirect(url_for('dashboard.seeker_dashboard'))

    # Query jobs posted by this employer along with applicant counts
    jobs_with_counts = (
        db.session.query(
            Job,
            func.count(Application.id).label('applicant_count')
        )
        .outerjoin(Application, Application.job_id == Job.id)
        .filter(Job.posted_by == user.id)
        .group_by(Job.id)
        .all()
    )

    # jobs_with_counts is a list of tuples (Job, applicant_count)
    # Pass it to template
    return render_template('jobs/my_posted_jobs.html', jobs_with_counts=jobs_with_counts)

# Employer View Applicants for a Job
@job_bp.route('/job/<int:job_id>/applicants')
def view_applicants(job_id):
    user = get_current_user()
    if not user:
        flash("You must be logged in to view applicants.", "danger")
        return redirect(url_for('auth.login'))

    if user.role != 'Employer':
        flash("Access denied.", "danger")
        return redirect(url_for('dashboard.seeker_dashboard'))

    job = Job.query.filter_by(id=job_id, posted_by=user.id).first()
    if not job:
        flash("Job not found or you don't have permission to view applicants.", "danger")
        return redirect(url_for('job.my_posted_jobs'))

    applications = job.applications  # assuming relationship Job.applications exists

    return render_template('jobs/view_applicants.html', job=job, applications=applications)


# Delete Job
@job_bp.route('/delete-job/<int:job_id>', methods=['POST'])
def delete_job(job_id):
    user = get_current_user()
    if not user:
        flash("Login required.", "danger")
        return redirect(url_for('auth.login'))
    
    if user.role != 'Employer':
        flash("Access denied. Only Employers can delete jobs.", "danger")
        return redirect(url_for('dashboard.seeker_dashboard'))

    job = Job.query.get_or_404(job_id)
    if job.posted_by != user.id:
        flash("Unauthorized action.", "danger")
        return redirect(url_for('job.my_jobs'))

    db.session.delete(job)
    db.session.commit()
    flash("Job deleted successfully!", "success")
    return redirect(url_for('job.my_jobs'))

@job_bp.route('/application/<int:app_id>/status', methods=['POST'])
def update_status(app_id):
    user = get_current_user()
    
    # Check if user is logged in
    if not user:
        flash('Please log in to perform this action.', 'danger')
        return redirect(url_for('auth.login'))

    application = Application.query.get_or_404(app_id)

    # Only the job poster can update the application status
    if user.id != application.job.posted_by:
        abort(403)

    new_status = request.form.get('status')
    if new_status:
        application.status = new_status
        db.session.commit()
        send_status_update_email(
            user_email=application.seeker.email,
            candidate_name=application.seeker.name,
            job_title=application.job.title,
            new_status=application.status
        )

        flash('Application status updated. Sent mail to applicant', 'success')

    return redirect(url_for('job.view_applicants', job_id=application.job.id))

# Edit Job
@job_bp.route('/edit-job/<int:job_id>', methods=['GET', 'POST'])
def edit_job(job_id):
    user = get_current_user()
    if not user:
        flash("Login required.", "danger")
        return redirect(url_for('auth.login'))
    if user.role != 'Employer':
        flash("Access denied. Only Employers can edit jobs.", "danger")
        return redirect(url_for('dashboard.seeker_dashboard'))

    job = Job.query.get_or_404(job_id)
    if job.posted_by != user.id:
        abort(403)

    if request.method == 'POST':
        job.title = request.form.get('title')
        job.description = request.form.get('description')
        job.location = request.form.get('location')
        job.job_type = request.form.get('job_type')
        salary = request.form.get('salary')

        try:
            job.salary = float(salary)
        except ValueError:
            flash("Salary must be a number.", "warning")
            return render_template('jobs/post_job.html', job=job)

        db.session.commit()
        flash("Job updated successfully!", "success")
        return redirect(url_for('job.my_posted_jobs'))

    return render_template('jobs/post_job.html', job=job)



#Seeker realted job functions
# SHows the seeker dashboard with their applications
@job_bp.route('/application')
def my_applications():
    user = get_current_user()

    if not user:
        flash("You must be logged in to access the dashboard.", "danger")
        return redirect(url_for('auth.login'))

    if user.role != 'Job Seeker':
        flash("Access denied. Only job seekers can access this page.", "danger")
        return redirect(url_for('job.post_job'))  # or any employer route

    applications = Application.query.filter_by(seeker_id=user.id).all()
    return render_template('jobs/seeker_applications.html', applications=applications)


# Apply to a job with cover letter and resume
@job_bp.route('/apply/<int:job_id>', methods=['POST'])
def apply_to_job(job_id):
    job = Job.query.get_or_404(job_id)
    user = get_current_user()

    # Ensure user is logged in
    if not user:
        flash('Please log in to apply for jobs.', 'danger')
        return redirect(url_for('auth.login'))

    # Ensure user is a seeker
    if user.role != 'Job Seeker':
        flash("Access denied. Only job seekers can access this page.", "danger")
        return redirect(url_for('job.post_job'))  # or any employer route

    # Prevent duplicate applications
    existing_application = Application.query.filter_by(job_id=job_id, seeker_id=user.id).first()
    if existing_application:
        flash('You have already applied for this job.', 'warning')
        return redirect(url_for('dashboard.seeker_dashboard'))


    # Get cover letter from form
    cover_letter = request.form.get('cover_letter')
    file = request.files['resume']

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(save_path)
        relative_path = os.path.join('uploads', filename).replace('\\', '/')
    else:
        flash('Invalid file type. Allowed: pdf', 'danger')
        return redirect(url_for('dashboard.seeker_dashboard'))


    # Create a new application
    application = Application(
        job_id=job.id,
        seeker_id=user.id,
        application_date=datetime.utcnow(),
        status='Pending',
        cover_letter=cover_letter,
        resume_path=relative_path
    )
    db.session.add(application)
    db.session.commit()

    # Send confirmation email to the seeker
    send_application_confirmation_email(
        user_email=user.email,
        candidate_name=user.name,
        job_title=job.title,
        company_name=job.poster.name
    )

    flash('Application submitted successfully.', 'success')
    return redirect(url_for('dashboard.seeker_dashboard'))

# Delete Application
@job_bp.route('/delete-application/<int:app_id>', methods=['POST'])
def delete_application(app_id):
    user = get_current_user()
    if not user or user.role != 'Job Seeker':
        flash("Unauthorized access.", "danger")
        return redirect(url_for('auth.login'))

    application = Application.query.get_or_404(app_id)

    # Only allow the seeker who applied to delete it
    if application.seeker_id != user.id:
        flash("You can only delete your own applications.", "danger")
        return redirect(url_for('job.my_applications'))

    db.session.delete(application)
    db.session.commit()

    flash("Application deleted successfully.", "success")
    return redirect(url_for('job.my_applications'))


# Show My Posted Jobs
@job_bp.route('/my-jobs')
def my_jobs():
    user = get_current_user()
    if not user:
        flash("Login required to view jobs.", "danger")
        return redirect(url_for('auth.login'))
    
    if user.role != 'Employer':
        flash("Access denied. Only Employers can view their jobs.", "danger")
        return redirect(url_for('dashboard.seeker_dashboard'))

    jobs = Job.query.filter_by(posted_by=user.id).all()
    return render_template('jobs/list_all_jobs.html', jobs=jobs)





