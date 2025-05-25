from flask import Blueprint, request, render_template, url_for, redirect, flash, session
from flask_jwt_extended import create_access_token
from datetime import timedelta
from .models import db, User

auth_bp = Blueprint('auth', __name__, template_folder='templates')


# Function to register Employer or Seeker
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')

        if User.query.filter_by(email=email).first():
            flash('User already exists', 'danger')
            return render_template('auth/register.html')


        new_user = User(email=email, role=role)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful. Please log in.", "success")
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')

#Function to Login Employer or Seeker
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        
        user = User.query.filter_by(email=email, role=role).first()

        if user and user.check_password(password):
            # Create a JWT access token
            access_token = create_access_token(identity={'id': user.id, 'role': user.role}, expires_delta=timedelta(hours=1))
            # Store token in session(CLient-Side Storage)
            session['access_token'] = access_token

            if role == "Employer":
                return redirect(url_for('dashboard.employer_dashboard'))
            else:
                return redirect(url_for('dashboard.seeker_dashboard'))
        else:
            flash('Invalid credentials or role mismatch', 'danger')
            return render_template('auth/login.html')
        
    return render_template('auth/login.html')

# Function to logout Employer or Seeker
@auth_bp.route('/logout')
def logout():
    if 'access_token' in session:
        session.pop('access_token')
        flash("Logged out successfully", "success") 
    else:
        flash("You are not logged in", "warning")
    return redirect(url_for('auth.login'))
