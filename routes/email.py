# routes/email.py

from flask_mail import Message
from flask import current_app, render_template, flash
from routes import mail  # This is safe now

def send_application_confirmation_email(user_email, candidate_name, job_title, company_name):
    subject = f"Job Application Confirmation - {job_title}"
    body = render_template(
        "email/application_confirmation.html",
        candidate_name=candidate_name,
        job_title=job_title,
        company_name=company_name
    )
    msg = Message(
        subject=subject,
        recipients=[user_email],
        html=body,
        sender=current_app.config['MAIL_USERNAME']
    )
    try:
        mail.send(msg)
        flash("Confirmation email sent successfully.", "success")
    except Exception as e:
        flash("Failed to send confirmation email.", "danger")
        print("Email sending failed:", str(e))

def send_status_update_email(user_email, candidate_name, job_title, new_status):
    subject = f"Application Status Update - {job_title}"
    body = render_template(
        "email/status_update.html",
        candidate_name=candidate_name,
        job_title=job_title,
        new_status=new_status
    )
    msg = Message(
        subject=subject,
        recipients=[user_email],
        html=body,
        sender=current_app.config['MAIL_USERNAME']
    )
    try:
        mail.send(msg)
        flash("Status update email sent successfully.", "success")
    except Exception as e:
        flash("Failed to send status update email.", "danger")
        print("Email sending failed:", str(e))

