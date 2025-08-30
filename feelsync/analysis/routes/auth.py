from flask import Blueprint, render_template, request, flash, redirect, url_for, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from models.database_models import User, db, SystemLog
from datetime import datetime, timedelta
import re

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    return True, "Password is valid"

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        age = request.form.get('age', type=int)
        gender = request.form.get('gender', '').strip()
        
        # Validation
        errors = []
        
        if not username or len(username) < 3:
            errors.append("Username must be at least 3 characters long")
        
        if not validate_email(email):
            errors.append("Please enter a valid email address")
        
        is_valid_password, password_msg = validate_password(password)
        if not is_valid_password:
            errors.append(password_msg)
        
        if password != confirm_password:
            errors.append("Passwords do not match")
        
        if not age or age < current_app.config['MIN_AGE_REQUIREMENT']:
            errors.append(f"You must be at least {current_app.config['MIN_AGE_REQUIREMENT']} years old")
        
        if age and age > current_app.config['MAX_AGE_REQUIREMENT']:
            errors.append(f"This platform is designed for users up to {current_app.config['MAX_AGE_REQUIREMENT']} years old")
        
        # Check for existing users
        if User.query.filter_by(username=username).first():
            errors.append("Username already exists")
        
        if User.query.filter_by(email=email).first():
            errors.append("Email already registered")
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/register.html')
        
        # Check if user is a minor
        is_minor = age < 18
        requires_consent = is_minor and current_app.config['REQUIRE_PARENTAL_CONSENT']
        
        if requires_consent:
            # Store registration data in session for consent flow
            session['pending_registration'] = {
                'username': username,
                'email': email,
                'password': password,
                'age': age,
                'gender': gender,
                'is_minor': is_minor
            }
            flash('Since you are under 18, parental consent is required. Please proceed to the consent form.', 'info')
            return redirect(url_for('auth.parental_consent'))
        
        # Create user directly if no consent needed
        user = User(
            username=username,
            email=email,
            age=age,
            gender=gender,
            is_minor=is_minor,
            parental_consent=not is_minor,
            consent_date=datetime.utcnow() if not is_minor else None
        )
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            
            SystemLog.log('INFO', 'USER_REGISTRATION', f'New user registered: {username}', user_id=user.id)
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            SystemLog.log('ERROR', 'USER_REGISTRATION', f'Registration failed for {username}: {str(e)}')
            flash('Registration failed. Please try again.', 'error')
    
    return render_template('auth/register.html')

@auth_bp.route('/parental_consent', methods=['GET', 'POST'])
def parental_consent():
    """Parental consent form for minors"""
    if 'pending_registration' not in session:
        flash('No pending registration found.', 'error')
        return redirect(url_for('auth.register'))
    
    if request.method == 'POST':
        parent_name = request.form.get('parent_name', '').strip()
        parent_email = request.form.get('parent_email', '').strip().lower()
        parent_phone = request.form.get('parent_phone', '').strip()
        consent_given = request.form.get('consent_given') == 'on'
        understand_data_use = request.form.get('understand_data_use') == 'on'
        
        errors = []
        
        if not parent_name:
            errors.append("Parent/guardian name is required")
        
        if not validate_email(parent_email):
            errors.append("Please enter a valid parent/guardian email address")
        
        if not consent_given:
            errors.append("Parental consent is required")
        
        if not understand_data_use:
            errors
