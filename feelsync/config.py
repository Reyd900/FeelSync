import os
from datetime import timedelta

class Config:
    """Base configuration class"""
    
    # Basic Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'feelsync-development-key-2024'
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///feelsync.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    
    # Security Configuration
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    
    # Session Configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or SECRET_KEY
    JWT_EXPIRATION_DELTA = timedelta(hours=24)
    
    # ML Model Configuration
    ML_MODEL_PATH = os.path.join(os.path.dirname(__file__), 'models', 'trained')
    ML_RETRAIN_THRESHOLD = 100  # Number of new data points before retraining
    ML_CONFIDENCE_THRESHOLD = 0.6  # Minimum confidence for ML predictions
    
    # Game Configuration
    GAME_SESSION_TIMEOUT = 300  # 5 minutes in seconds
    MAX_GAME_SESSIONS_PER_DAY = 10
    MIN_GAME_DURATION = 30  # Minimum seconds for valid session
    
    # Data Privacy Configuration
    DATA_RETENTION_DAYS = 365  # How long to keep user data
    ANONYMIZATION_ENABLED = True
    EXPORT_DATA_ENABLED = True  # Allow users to export their data
    
    # Email Configuration (for notifications)
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'localhost'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # API Rate Limiting
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL') or 'memory://'
    RATELIMIT_DEFAULT = "100 per hour"
    
    # File Upload Configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
    
    # Logging Configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'feelsync.log')
    
    # Feature Flags
    ENABLE_THERAPIST_ACCESS = os.environ.get('ENABLE_THERAPIST_ACCESS', 'true').lower() == 'true'
    ENABLE_DATA_EXPORT = os.environ.get('ENABLE_DATA_EXPORT', 'true').lower() == 'true'
    ENABLE_ML_PREDICTIONS = os.environ.get('ENABLE_ML_PREDICTIONS', 'true').lower() == 'true'
    ENABLE_REPORT_GENERATION = os.environ.get('ENABLE_REPORT_GENERATION', 'true').lower() == 'true'
    
    # Behavioral Analysis Configuration
    ANALYSIS_CONFIG = {
        'min_sessions_for_trends': 3,
        'confidence_boost_threshold': 10,  # Number of sessions to boost confidence
        'anomaly_detection_threshold': 2.0,  # Standard deviations for anomaly detection
        'clustering_update_frequency': 50,  # Update clusters every N new data points
    }
    
    # Game-specific Configuration
    CATCH_THOUGHT_CONFIG = {
        'default_duration': 60,  # seconds
        'min_bubbles_for_analysis': 10,
        'reaction_time_threshold': 2000,  # ms for slow reaction
        'fast_reaction_threshold': 300,  # ms for fast reaction
    }
    
    STAT_BALANCE_CONFIG = {
        'default_duration': 120,  # seconds
        'decision_time_threshold': 3000,  # ms for slow decision
        'balance_threshold': 0.1,  # Acceptable imbalance ratio
    }
    
    DECISION_MAKER_CONFIG = {
        'scenarios_per_session': 10,
        'max_decision_time': 30,  # seconds per scenario
        'confidence_weight': 0.3,  # Weight for confidence scoring
    }

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    DEVELOPMENT = True
    
    # More lenient settings for development
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_ECHO = True  # Log SQL queries
    
    # Test data configuration
    CREATE_TEST_DATA = True
    TEST_USER_COUNT = 5
    
    # ML Configuration for development
    ML_RETRAIN_THRESHOLD = 10  # Lower threshold for testing
    
class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # In-memory database for tests
    
    # Disable external services during testing
    MAIL_SUPPRESS_SEND = True
    CELERY_ALWAYS_EAGER = True
    
    # Speed up password hashing for tests
    BCRYPT_LOG_ROUNDS = 4

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    
    # Security settings
    SESSION_COOKIE_SECURE = True
    WTF_CSRF_SSL_STRICT = True
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 300,
        'pool_pre_ping': True,
    }
    
    # Enhanced logging
    LOG_LEVEL = 'WARNING'
    
    # Stricter rate limiting
    RATELIMIT_DEFAULT = "50 per hour"
    
    # Performance optimizations
    SQLALCHEMY_RECORD_QUERIES = False

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

# Mental health assessment thresholds
MENTAL_HEALTH_THRESHOLDS = {
    'anxiety': {
        'low': 30,
        'moderate': 60,
        'high': 80
    },
    'depression': {
        'low': 30,
        'moderate': 60,  
        'high': 80
    },
    'attention': {
        'excellent': 80,
        'good': 60,
        'concerning': 40,
        'significant_difficulty': 20
    },
    'impulsivity': {
        'low': 30,
        'moderate': 60,
        'high': 80
    },
    'emotional_regulation': {
        'excellent': 80,
        'good': 60,
        'concerning': 40,
        'difficult': 20
    }
}

# Risk assessment configuration
RISK_ASSESSMENT_CONFIG = {
    'low_risk': {
        'max_score': 2,
        'description': 'Low risk indicators present',
        'action': 'Continue monitoring'
    },
    'moderate_risk': {
        'max_score': 5,
        'description': 'Moderate risk factors detected',
        'action': 'Consider professional consultation'
    },
    'high_risk': {
        'max_score': float('inf'),
        'description': 'High risk indicators present',
        'action': 'Strongly recommend professional help'
    }
}

# Behavioral cluster definitions
BEHAVIORAL_CLUSTERS = {
    'fast_accurate': {
        'name': 'Fast & Accurate',
        'description': 'Quick decision-makers with high accuracy',
        'characteristics': ['low_reaction_time', 'high_accuracy', 'consistent_performance']
    },
    'slow_consistent': {
        'name': 'Slow but Consistent',
        'description': 'Thoughtful players with steady performance',
        'characteristics': ['high_reaction_time', 'high_accuracy', 'low_variance']
    },
    'erratic': {
        'name': 'Erratic/Variable',
        'description': 'Variable performance with inconsistent patterns',
        'characteristics': ['high_variance', 'moderate_accuracy', 'emotional_reactivity']
    }
}

# Data validation rules
DATA_VALIDATION_RULES = {
    'reaction_time': {
        'min': 100,  # Minimum possible reaction time (ms)
        'max': 10000,  # Maximum reasonable reaction time (ms)
        'outlier_threshold': 3  # Standard deviations for outlier detection
    },
    'accuracy': {
        'min': 0.0,
        'max': 1.0
    },
    'session_duration': {
        'min': 30,  # Minimum valid session (seconds)
        'max': 1800  # Maximum session length (30 minutes)
    },
    'score_ranges': {
        'anxiety': {'min': 0, 'max': 100},
        'depression': {'min': 0, 'max': 100},
        'attention': {'min': 0, 'max': 100},
        'impulsivity': {'min': 0, 'max': 100}
    }
}

# Consent and privacy settings
CONSENT_CONFIG = {
    'required_age_for_self_consent': 18,
    'data_retention_period_days': 365,
    'allow_data_deletion': True,
    'allow_data_export': True,
    'anonymization_delay_days': 30,  # Days before data is anonymized
    'consent_version': '1.0',
    'required_consents': [
        'data_collection',
        'behavioral_analysis', 
        'research_participation'
    ],
    'optional_consents': [
        'marketing_communications',
        'third_party_sharing',
        'extended_data_retention'
    ]
}

# Notification settings
NOTIFICATION_CONFIG = {
    'enabled': True,
    'channels': ['email', 'in_app'],
    'triggers': {
        'high_risk_detected': {
            'enabled': True,
            'threshold': 'high_risk',
            'delay_hours': 1
        },
        'unusual_pattern': {
            'enabled': True,
            'threshold': 'moderate_change',
            'delay_hours': 24
        },
        'session_reminder': {
            'enabled': True,
            'days_inactive': 7
        }
    }
}

# API versioning
API_CONFIG = {
    'current_version': 'v1',
    'supported_versions': ['v1'],
    'deprecation_warnings': {},
    'rate_limits': {
        'default': '100/hour',
        'authenticated': '500/hour',
        'therapist': '1000/hour'
    }
}
