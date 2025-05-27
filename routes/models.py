from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Employer and Seeker User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(512), nullable=False)
    role = db.Column(db.String(20), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(120))
    job_type = db.Column(db.String(50))
    salary = db.Column(db.Float)
    posted_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    poster = db.relationship('User', backref='jobs', foreign_keys=[posted_by])
    applications = db.relationship('Application', back_populates='job')


class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'))
    seeker_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    cover_letter = db.Column(db.Text)
    resume_path = db.Column(db.String(200))
    
    job = db.relationship('Job', back_populates='applications')
    seeker = db.relationship('User')  # adjust if you want a backref here

