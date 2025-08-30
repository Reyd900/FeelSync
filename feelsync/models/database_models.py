from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()

class User(db.Model):
    """User model for storing user information and consent data"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Demographics
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(20), nullable=True)
    location = db.Column(db.String(100), nullable=True)
    
    # Consent and Privacy
    consent_given = db.Column(db.Boolean, default=False, nullable=False)
    parental_consent = db.Column(db.Boolean, default=False, nullable=False)
    data_sharing_consent = db.Column(db.Boolean, default=False, nullable=False)
    
    # Account Settings
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_therapist = db.Column(db.Boolean, default=False, nullable=False)
    anonymized_id = db.Column(db.String(36), unique=True, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    game_sessions = db.relationship('GameSession', backref='user', lazy=True, cascade='all, delete-orphan')
    behavior_analyses = db.relationship('BehaviorAnalysis', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def is_minor(self):
        """Check if user is a minor"""
        return self.age < 18
    
    def can_participate(self):
        """Check if user can participate in games"""
        if not self.consent_given:
            return False
        if self.is_minor() and not self.parental_consent:
            return False
        return True
    
    def to_dict(self):
        """Convert user to dictionary (excluding sensitive data)"""
        return {
            'id': self.id,
            'username': self.username,
            'age': self.age,
            'gender': self.gender,
            'created_at': self.created_at.isoformat(),
            'is_minor': self.is_minor(),
            'anonymized_id': self.anonymized_id
        }

class GameSession(db.Model):
    """Model for storing individual game session data"""
    __tablename__ = 'game_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Game Information
    game_type = db.Column(db.String(50), nullable=False)  # 'catch_thought', 'stat_balance', 'decision_maker'
    version = db.Column(db.String(10), default='1.0')
    
    # Session Data
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    duration = db.Column(db.Integer)  # Duration in seconds
    completed = db.Column(db.Boolean, default=False)
    
    # Game Results
    score = db.Column(db.Integer, default=0)
    level_reached = db.Column(db.Integer, default=1)
    accuracy = db.Column(db.Float, default=0.0)
    
    # Behavioral Data (JSON stored as text)
    game_data = db.Column(db.Text)  # JSON string containing all behavioral data
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    device_info = db.Column(db.String(200))
    browser_info = db.Column(db.String(200))
    
    # Relationships
    behavior_analysis = db.relationship('BehaviorAnalysis', backref='session', uselist=False)
    
    def get_game_data(self):
        """Get parsed game data"""
        if self.game_data:
            return json.loads(self.game_data)
        return {}
    
    def set_game_data(self, data):
        """Set game data as JSON"""
        self.game_data = json.dumps(data)
    
    def get_duration_minutes(self):
        """Get duration in minutes"""
        if self.duration:
            return round(self.duration / 60, 2)
        return 0
    
    def to_dict(self):
        """Convert session to dictionary"""
        return {
            'id': self.id,
            'game_type': self.game_type,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.duration,
            'completed': self.completed,
            'score': self.score,
            'accuracy': self.accuracy,
            'behavioral_data': self.get_game_data()
        }

class BehaviorAnalysis(db.Model):
    """Model for storing ML analysis results"""
    __tablename__ = 'behavior_analyses'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('game_sessions.id'), nullable=True)
    
    # Mental Health Indicators (0-100 scale)
    anxiety_score = db.Column(db.Float, default=0.0)
    depression_score = db.Column(db.Float, default=0.0)
    attention_score = db.Column(db.Float, default=0.0)  # ADHD-like indicators
    impulsivity_score = db.Column(db.Float, default=0.0)
    emotional_regulation_score = db.Column(db.Float, default=0.0)
    
    # Behavioral Patterns
    reaction_time_avg = db.Column(db.Float)
    reaction_time_variance = db.Column(db.Float)
    decision_consistency = db.Column(db.Float)
    error_rate = db.Column(db.Float)
    hesitation_frequency = db.Column(db.Float)
    
    # ML Model Results
    predicted_cluster = db.Column(db.String(20))  # 'fast_accurate', 'slow_consistent', 'erratic'
    confidence_score = db.Column(db.Float, default=0.0)
    
    # Detailed Analysis (JSON)
    analysis_data = db.Column(db.Text)  # Detailed analysis results
    insights = db.Column(db.Text)  # Human-readable insights
    
    # Risk Assessment
    risk_level = db.Column(db.String(10), default='low')  # 'low', 'medium', 'high'
    requires_attention = db.Column(db.Boolean, default=False)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    model_version = db.Column(db.String(10), default='1.0')
    
    def get_analysis_data(self):
        """Get parsed analysis data"""
        if self.analysis_data:
            return json.loads(self.analysis_data)
        return {}
    
    def set_analysis_data(self, data):
        """Set analysis data as JSON"""
        self.analysis_data = json.dumps(data)
    
    def get_insights_list(self):
        """Get insights as a list"""
        if self.insights:
            return json.loads(self.insights)
        return []
    
    def set_insights(self, insights_list):
        """Set insights from a list"""
        self.insights = json.dumps(insights_list)
    
    def get_overall_score(self):
        """Calculate overall mental health indicator score"""
        scores = [
            self.anxiety_score,
            self.depression_score,
            100 - self.attention_score,  # Higher attention = better
            self.impulsivity_score,
            100 - self.emotional_regulation_score  # Higher regulation = better
        ]
        return sum(scores) / len(scores)
    
    def get_risk_indicators(self):
        """Get list of risk indicators"""
        indicators = []
        
        if self.anxiety_score > 70:
            indicators.append("High anxiety patterns detected")
        if self.depression_score > 70:
            indicators.append("Potential depressive tendencies")
        if self.attention_score < 30:
            indicators.append("Attention difficulties observed")
        if self.impulsivity_score > 70:
            indicators.append("Impulsive behavior patterns")
        if self.emotional_regulation_score < 30:
            indicators.append("Emotional regulation challenges")
        
        return indicators
    
    def to_dict(self):
        """Convert analysis to dictionary"""
        return {
            'id': self.id,
            'created_at': self.created_at.isoformat(),
            'anxiety_score': self.anxiety_score,
            'depression_score': self.depression_score,
            'attention_score': self.attention_score,
            'impulsivity_score': self.impulsivity_score,
            'emotional_regulation_score': self.emotional_regulation_score,
            'predicted_cluster': self.predicted_cluster,
            'confidence_score': self.confidence_score,
            'risk_level': self.risk_level,
            'overall_score': self.get_overall_score(),
            'risk_indicators': self.get_risk_indicators(),
            'insights': self.get_insights_list()
        }

class ConsentRecord(db.Model):
    """Model for tracking consent history"""
    __tablename__ = 'consent_records'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    consent_type = db.Column(db.String(50), nullable=False)  # 'data_collection', 'parental', 'research'
    consent_given = db.Column(db.Boolean, nullable=False)
    consent_text = db.Column(db.Text)  # The consent text shown to user
    
    # Legal/Audit Trail
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='consent_records')

class TherapistAccess(db.Model):
    """Model for managing therapist access to user data"""
    __tablename__ = 'therapist_access'
    
    id = db.Column(db.Integer, primary_key=True)
    therapist_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    access_granted = db.Column(db.Boolean, default=False)
    access_level = db.Column(db.String(20), default='basic')  # 'basic', 'full'
    
    granted_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    
    # Relationships
    therapist = db.relationship('User', foreign_keys=[therapist_id], backref='therapist_accesses')
    patient
