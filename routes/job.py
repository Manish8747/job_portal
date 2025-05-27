from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort
from flask_jwt_extended import decode_token
from .models import db, User, Job, Application
import os
from werkzeug.utils import secure_filename
from sqlalchemy import func

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
            print("[TOKEN DECODED]", decoded)
            print("[USER ID]", user_id, "[USER ROLE]", user_role)
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
    return render_template('jobs/list_jobs.html', jobs=jobs)



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

# List all jobs for seekers posted by all Employers
@job_bp.route('/jobs')
def list_all_jobs():
    user = get_current_user()
    jobs = Job.query.all()
    return render_template('jobs/seeker_job_list.html', jobs=jobs, user=user)


# Apply to a job with cover letter and resume
@job_bp.route('/apply/<int:job_id>', methods=['POST'])
def apply_to_job(job_id):
    user = get_current_user()
    if not user or user.role != 'Job Seeker':
        flash("Only seekers can apply to jobs.", "danger")
        return redirect(url_for('auth.login'))

    job = Job.query.get_or_404(job_id)

    cover_letter = request.form.get('cover_letter')
    resume = request.files.get('resume')

    if not cover_letter or not resume or not allowed_file(resume.filename):
        flash("Invalid input. Please provide a cover letter and PDF resume.", "warning")
        return redirect(url_for('dashboard.seeker_dashboard'))

    # Save resume
    filename = secure_filename(resume.filename)
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    save_path = os.path.join(UPLOAD_FOLDER, filename)
    resume.save(save_path)

    # Save relative path for database (use forward slashes for URLs)
    # Remove 'static/' prefix because url_for('static') already points to it
    relative_path = os.path.join('uploads', filename).replace('\\', '/')

    application = Application(
        job_id=job.id,
        seeker_id=user.id,
        cover_letter=cover_letter,
        resume_path=relative_path  # store relative path only
    )
    db.session.add(application)
    db.session.commit()

    flash("Application submitted successfully!", "success")
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
