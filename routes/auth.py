from flask import Blueprint, request, jsonify, render_template, url_for, redirect
from flask_jwt_extended import create_access_token
from .models import db,User

auth_bp = Blueprint('auth', __name__, template_folder='templates')

@auth_bp.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        
        if not email or not password or not role:
            return jsonify({'message': 'Missing required fields'}), 400
        
        if User.query.filter_by(email=email).first():
            return jsonify({'message': 'User already exists'}), 400
        
        new_user = User(email=email, role=role)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Handle login logic here
        pass
    return render_template('auth/login.html')


