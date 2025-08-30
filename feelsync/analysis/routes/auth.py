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
            errors.append("You must acknowledge understanding of data use")
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/consent.html')
        
        # Create user with parental consent
        reg_data = session['pending_registration']
        user = User(
            username=reg_data['username'],
            email=reg_data['email'],
            age=reg_data['age'],
            gender=reg_data['gender'],
            is_minor=reg_data['is_minor'],
            parental_consent=True,
            consent_date=datetime.utcnow()
        )
        user.set_password(reg_data['password'])
        
        try:
            db.session.add(user)
            db.session.commit()
            
            # Clear pending registration
            session.pop('pending_registration', None)
            
            SystemLog.log('INFO', 'USER_REGISTRATION', 
                         f'Minor user registered with parental consent: {user.username}', 
                         user_id=user.id,
                         parent_email=parent_email, parent_name=parent_name)
            
            flash('Registration successful with parental consent! Please log in.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            SystemLog.log('ERROR', 'USER_REGISTRATION', 
                         f'Registration failed for minor {reg_data["username"]}: {str(e)}')
            flash('Registration failed. Please try again.', 'error')
    
    return render_template('auth/consent.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        username_or_email = request.form.get('username_or_email', '').strip().lower()
        password = request.form.get('password', '')
        remember_me = request.form.get('remember_me') == 'on'
        
        if not username_or_email or not password:
            flash('Please enter both username/email and password.', 'error')
            return render_template('auth/login.html')
        
        # Try to find user by username or email
        user = User.query.filter(
            (User.username == username_or_email) | 
            (User.email == username_or_email)
        ).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact support.', 'error')
                SystemLog.log('WARNING', 'LOGIN_ATTEMPT', 
                             f'Login attempt on deactivated account: {user.username}', 
                             user_id=user.id)
                return render_template('auth/login.html')
            
            # Update last login
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            login_user(user, remember=remember_me)
            
            SystemLog.log('INFO', 'USER_LOGIN', f'User logged in: {user.username}', user_id=user.id)
            
            # Redirect to next page if available
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('dashboard.index'))
        else:
            flash('Invalid username/email or password.', 'error')
            SystemLog.log('WARNING', 'LOGIN_FAILED', 
                         f'Failed login attempt for: {username_or_email}')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    username = current_user.username
    user_id = current_user.id
    
    logout_user()
    session.clear()
    
    SystemLog.log('INFO', 'USER_LOGOUT', f'User logged out: {username}', user_id=user_id)
    
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))

@auth_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    return render_template('auth/profile.html', user=current_user)

@auth_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit user profile"""
    if request.method == 'POST':
        # Update allowed fields only
        gender = request.form.get('gender', '').strip()
        data_sharing_consent = request.form.get('data_sharing_consent') == 'on'
        analytics_consent = request.form.get('analytics_consent') == 'on'
        
        current_user.gender = gender
        current_user.data_sharing_consent = data_sharing_consent
        current_user.analytics_consent = analytics_consent
        
        try:
            db.session.commit()
            SystemLog.log('INFO', 'PROFILE_UPDATE', 
                         f'Profile updated for user: {current_user.username}', 
                         user_id=current_user.id)
            flash('Profile updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            SystemLog.log('ERROR', 'PROFILE_UPDATE', 
                         f'Profile update failed for {current_user.username}: {str(e)}', 
                         user_id=current_user.id)
            flash('Profile update failed. Please try again.', 'error')
        
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/edit_profile.html', user=current_user)

@auth_bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change user password"""
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        errors = []
        
        if not current_user.check_password(current_password):
            errors.append("Current password is incorrect")
        
        is_valid_password, password_msg = validate_password(new_password)
        if not is_valid_password:
            errors.append(password_msg)
        
        if new_password != confirm_password:
            errors.append("New passwords do not match")
        
        if current_password == new_password:
            errors.append("New password must be different from current password")
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/change_password.html')
        
        # Update password
        current_user.set_password(new_password)
        
        try:
            db.session.commit()
            SystemLog.log('INFO', 'PASSWORD_CHANGE', 
                         f'Password changed for user: {current_user.username}', 
                         user_id=current_user.id)
            flash('Password changed successfully!', 'success')
            return redirect(url_for('auth.profile'))
        except Exception as e:
            db.session.rollback()
            SystemLog.log('ERROR', 'PASSWORD_CHANGE', 
                         f'Password change failed for {current_user.username}: {str(e)}', 
                         user_id=current_user.id)
            flash('Password change failed. Please try again.', 'error')
    
    return render_template('auth/change_password.html')

@auth_bp.route('/delete_account', methods=['GET', 'POST'])
@login_required
def delete_account():
    """Delete user account"""
    if request.method == 'POST':
        password = request.form.get('password', '')
        confirmation = request.form.get('confirmation', '').strip()
        
        if not current_user.check_password(password):
            flash('Incorrect password.', 'error')
            return render_template('auth/delete_account.html')
        
        if confirmation.lower() != 'delete my account':
            flash('Please type "delete my account" to confirm.', 'error')
            return render_template('auth/delete_account.html')
        
        username = current_user.username
        user_id = current_user.id
        
        try:
            # Log the deletion before removing the user
            SystemLog.log('INFO', 'ACCOUNT_DELETION', 
                         f'Account deleted for user: {username}', 
                         user_id=user_id)
            
            # Delete user (cascade will handle related data)
            db.session.delete(current_user)
            db.session.commit()
            
            logout_user()
            session.clear()
            
            flash('Your account has been deleted successfully.', 'info')
            return redirect(url_for('index'))
            
        except Exception as e:
            db.session.rollback()
            SystemLog.log('ERROR', 'ACCOUNT_DELETION', 
                         f'Account deletion failed for {username}: {str(e)}', 
                         user_id=user_id)
            flash('Account deletion failed. Please try again or contact support.', 'error')
    
    return render_template('auth/delete_account.html')

@auth_bp.route('/data_export')
@login_required
def data_export():
    """Export user data (GDPR compliance)"""
    try:
        # Gather user data
        user_data = {
            'profile': {
                'username': current_user.username,
                'email': current_user.email,
                'age': current_user.age,
                'gender': current_user.gender,
                'created_at': current_user.created_at.isoformat() if current_user.created_at else None,
                'last_login': current_user.last_login.isoformat() if current_user.last_login else None
            },
            'game_sessions': [],
            'behavior_data': [],
            'analysis_reports': []
        }
        
        # Add game sessions
        for session in current_user.game_sessions:
            session_data = {
                'game_type': session.game_type,
                'started_at': session.started_at.isoformat() if session.started_at else None,
                'ended_at': session.ended_at.isoformat() if session.ended_at else None,
                'duration': session.duration,
                'score': session.score,
                'completed': session.completed
            }
            user_data['game_sessions'].append(session_data)
        
        # Add behavior data (anonymized)
        for behavior in current_user.behavior_data:
            behavior_data = {
                'timestamp': behavior.timestamp.isoformat() if behavior.timestamp else None,
                'reaction_time': behavior.reaction_time,
                'decision_type': behavior.decision_type,
                'game_level': behavior.game_level
            }
            user_data['behavior_data'].append(behavior_data)
        
        # Add analysis reports
        for report in current_user.analysis_reports:
            report_data = {
                'generated_at': report.generated_at.isoformat() if report.generated_at else None,
                'report_type': report.report_type,
                'summary': report.summary
            }
            user_data['analysis_reports'].append(report_data)
        
        SystemLog.log('INFO', 'DATA_EXPORT', 
                     f'Data exported for user: {current_user.username}', 
                     user_id=current_user.id)
        
        return render_template('auth/data_export.html', data=user_data)
        
    except Exception as e:
        SystemLog.log('ERROR', 'DATA_EXPORT', 
                     f'Data export failed for {current_user.username}: {str(e)}', 
                     user_id=current_user.id)
        flash('Data export failed. Please try again.', 'error')
        return redirect(url_for('auth.profile'))
