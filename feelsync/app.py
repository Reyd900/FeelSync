from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_migrate import Migrate
from datetime import datetime, timedelta
import os
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from functools import wraps
import json

# Import custom modules
from models.database_models import db, User, GameSession, BehaviorAnalysis
from models.ml_models import BehaviorPredictor
from models.behavior_analyzer import BehaviorAnalyzer
from utils.report_generator import ReportGenerator

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'feelsync-dev-key-2024')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///feelsync.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
CORS(app)
migrate = Migrate(app, db)

# Initialize ML components
behavior_predictor = BehaviorPredictor()
behavior_analyzer = BehaviorAnalyzer()
report_generator = ReportGenerator()

def token_required(f):
    """Decorator for routes that require authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
        
        return f(current_user, *args, **kwargs)
    return decorated

@app.route('/')
def index():
    """Landing page"""
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """User dashboard"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    recent_sessions = GameSession.query.filter_by(user_id=user.id).order_by(
        GameSession.created_at.desc()
    ).limit(5).all()
    
    # Get latest analysis
    latest_analysis = BehaviorAnalysis.query.filter_by(user_id=user.id).order_by(
        BehaviorAnalysis.created_at.desc()
    ).first()
    
    return render_template('dashboard.html', 
                         user=user, 
                         recent_sessions=recent_sessions,
                         latest_analysis=latest_analysis)

# Authentication Routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        # Validate input
        if not data.get('username') or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Check if user exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already registered'}), 400
        
        # Create new user
        user = User(
            username=data['username'],
            email=data['email'],
            password_hash=generate_password_hash(data['password']),
            age=data.get('age', 16),
            consent_given=data.get('consent', False),
            parental_consent=data.get('parental_consent', False) if int(data.get('age', 18)) < 18 else True
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Generate token
        token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, app.config['SECRET_KEY'])
        
        return jsonify({'token': token, 'user_id': user.id})
    
    return render_template('auth/register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        user = User.query.filter_by(email=data['email']).first()
        
        if user and check_password_hash(user.password_hash, data['password']):
            session['user_id'] = user.id
            
            # Generate token for API access
            token = jwt.encode({
                'user_id': user.id,
                'exp': datetime.utcnow() + timedelta(hours=24)
            }, app.config['SECRET_KEY'])
            
            if request.is_json:
                return jsonify({'token': token, 'user_id': user.id})
            else:
                return redirect(url_for('dashboard'))
        
        error = 'Invalid credentials'
        if request.is_json:
            return jsonify({'error': error}), 401
        return render_template('auth/login.html', error=error)
    
    return render_template('auth/login.html')

@app.route('/logout')
def logout():
    """User logout"""
    session.pop('user_id', None)
    return redirect(url_for('index'))

# Game Routes
@app.route('/games/catch-thought')
def catch_thought_game():
    """Catch the Thought game"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('games/catch_thought.html')

@app.route('/games/stat-balance')
def stat_balance_game():
    """Stat Balancing game"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('games/stat_balance.html')

@app.route('/games/decision-maker')
def decision_maker_game():
    """Decision Making game"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('games/decision_maker.html')

# API Routes for Game Data
@app.route('/api/games/session', methods=['POST'])
@token_required
def create_game_session(current_user):
    """Create a new game session"""
    data = request.get_json()
    
    session_obj = GameSession(
        user_id=current_user.id,
        game_type=data['game_type'],
        start_time=datetime.utcnow()
    )
    
    db.session.add(session_obj)
    db.session.commit()
    
    return jsonify({'session_id': session_obj.id})

@app.route('/api/games/session/<int:session_id>/data', methods=['POST'])
@token_required
def save_game_data(current_user, session_id):
    """Save game session data"""
    data = request.get_json()
    
    session_obj = GameSession.query.get(session_id)
    if not session_obj or session_obj.user_id != current_user.id:
        return jsonify({'error': 'Session not found'}), 404
    
    # Update session with game data
    session_obj.score = data.get('score', 0)
    session_obj.duration = data.get('duration', 0)
    session_obj.game_data = json.dumps(data.get('behavioral_data', {}))
    session_obj.end_time = datetime.utcnow()
    session_obj.completed = True
    
    db.session.commit()
    
    # Trigger behavioral analysis
    behavioral_data = data.get('behavioral_data', {})
    analysis_result = behavior_analyzer.analyze_session(behavioral_data)
    
    # Save analysis
    analysis = BehaviorAnalysis(
        user_id=current_user.id,
        session_id=session_id,
        anxiety_score=analysis_result.get('anxiety_score', 0),
        depression_score=analysis_result.get('depression_score', 0),
        attention_score=analysis_result.get('attention_score', 0),
        impulsivity_score=analysis_result.get('impulsivity_score', 0),
        analysis_data=json.dumps(analysis_result)
    )
    
    db.session.add(analysis)
    db.session.commit()
    
    return jsonify({
        'message': 'Data saved successfully',
        'analysis_id': analysis.id,
        'preliminary_insights': analysis_result.get('insights', [])
    })

@app.route('/api/analysis/<int:user_id>')
@token_required
def get_user_analysis(current_user, user_id):
    """Get behavioral analysis for a user"""
    if current_user.id != user_id and not current_user.is_therapist:
        return jsonify({'error': 'Unauthorized'}), 403
    
    analyses = BehaviorAnalysis.query.filter_by(user_id=user_id).order_by(
        BehaviorAnalysis.created_at.desc()
    ).limit(10).all()
    
    analysis_data = []
    for analysis in analyses:
        analysis_data.append({
            'id': analysis.id,
            'date': analysis.created_at.isoformat(),
            'anxiety_score': analysis.anxiety_score,
            'depression_score': analysis.depression_score,
            'attention_score': analysis.attention_score,
            'impulsivity_score': analysis.impulsivity_score,
            'insights': json.loads(analysis.analysis_data).get('insights', [])
        })
    
    return jsonify(analysis_data)

@app.route('/api/report/<int:user_id>')
@token_required
def generate_report(current_user, user_id):
    """Generate comprehensive behavioral report"""
    if current_user.id != user_id and not current_user.is_therapist:
        return jsonify({'error': 'Unauthorized'}), 403
    
    user = User.query.get(user_id)
    analyses = BehaviorAnalysis.query.filter_by(user_id=user_id).order_by(
        BehaviorAnalysis.created_at.desc()
    ).all()
    
    sessions = GameSession.query.filter_by(user_id=user_id, completed=True).order_by(
        GameSession.created_at.desc()
    ).all()
    
    report_data = report_generator.generate_comprehensive_report(user, analyses, sessions)
    
    return jsonify(report_data)

@app.route('/analysis/personal')
def personal_analysis():
    """Personal analysis page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    analyses = BehaviorAnalysis.query.filter_by(user_id=user.id).order_by(
        BehaviorAnalysis.created_at.desc()
    ).all()
    
    return render_template('analysis/personal_report.html', user=user, analyses=analyses)

@app.route('/therapist/dashboard')
def therapist_dashboard():
    """Therapist dashboard (restricted access)"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    if not user.is_therapist:
        return jsonify({'error': 'Access denied'}), 403
    
    # Get users with recent activity
    recent_users = db.session.query(User).join(GameSession).filter(
        GameSession.created_at > datetime.utcnow() - timedelta(days=30)
    ).distinct().all()
    
    return render_template('analysis/therapist_view.html', users=recent_users)

# Error Handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

# Database initialization
@app.before_first_request
def create_tables():
    db.create_all()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    app.run(debug=True, host='0.0.0.0', port=5000)
