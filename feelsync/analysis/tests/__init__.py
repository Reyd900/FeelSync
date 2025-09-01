# tests/__init__.py
"""
Test package for FeelSync application
Contains unit tests, integration tests, and test utilities
"""

import pytest
import tempfile
import os
from app import create_app
from models.database_models import db, User, GameSession, BehaviorData
from config import TestingConfig

@pytest.fixture(scope='session')
def app():
    """Create application for testing"""
    # Create temporary database
    db_fd, db_path = tempfile.mkstemp()
    
    # Update config for testing
    TestingConfig.SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'
    
    app = create_app(TestingConfig)
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()
    
    # Clean up
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Create test CLI runner"""
    return app.test_cli_runner()

@pytest.fixture
def auth_client(client, app):
    """Create authenticated test client"""
    with app.app_context():
        # Create test user
        user = User(
            username='testuser',
            email='test@example.com',
            age=20,
            is_minor=False,
            parental_consent=True
        )
        user.set_password('TestPassword123')
        db.session.add(user)
        db.session.commit()
        
        # Login
        client.post('/auth/login', data={
            'username_or_email': 'testuser',
            'password': 'TestPassword123'
        })
        
        yield client, user

@pytest.fixture
def sample_game_session(app):
    """Create sample game session for testing"""
    with app.app_context():
        user = User.query.filter_by(username='testuser').first()
        if not user:
            user = User(
                username='testuser',
                email='test@example.com',
                age=20
            )
            user.set_password('TestPassword123')
            db.session.add(user)
            db.session.commit()
        
        session = GameSession(
            user_id=user.id,
            game_type='catch_thought',
            score=100,
            duration=300,
            completed=True,
            accuracy=0.85,
            average_reaction_time=250.5
        )
        db.session.add(session)
        db.session.commit()
        
        return session

class TestHelpers:
    """Helper functions for tests"""
    
    @staticmethod
    def create_test_user(username='testuser', email='test@example.com', age=20):
        """Create a test user"""
        user = User(
            username=username,
            email=email,
            age=age,
            is_minor=age < 18,
            parental_consent=True
        )
        user.set_password('TestPassword123')
        db.session.add(user)
        db.session.commit()
        return user
    
    @staticmethod
    def create_test_session(user_id, game_type='catch_thought', score=100):
        """Create a test game session"""
        session = GameSession(
            user_id=user_id,
            game_type=game_type,
            score=score,
            duration=300,
            completed=True,
            accuracy=0.85,
            average_reaction_time=250.5
        )
        db.session.add(session)
        db.session.commit()
        return session
    
    @staticmethod
    def create_test_behavior_data(user_id, session_id):
        """Create test behavior data"""
        behavior = BehaviorData(
            user_id=user_id,
            session_id=session_id,
            reaction_time=250.0,
            decision_type='positive_choice',
            decision_value='help_friend',
            accuracy=True,
            stress_level=3
        )
        db.session.add(behavior)
        db.session.commit()
        return behavior

# Test configuration constants
TEST_CONFIG = {
    'TESTING': True,
    'WTF_CSRF_ENABLED': False,
    'LOGIN_DISABLED': False,
    'MAIL_SUPPRESS_SEND': True
}

# Common test data
SAMPLE_USER_DATA = {
    'username': 'testuser',
    'email': 'test@example.com',
    'password': 'TestPassword123',
    'age': 20,
    'gender': 'other'
}

SAMPLE_GAME_DATA = {
    'catch_thought': {
        'final_score': 150,
        'level_reached': 3,
        'accuracy': 0.87,
        'average_reaction_time': 245.2,
        'decisions_made': 25
    },
    'stat_balance': {
        'final_score': 200,
        'level_reached': 5,
        'accuracy': 0.92,
        'average_reaction_time': 180.5,
        'decisions_made': 15
    },
    'decision_maker': {
        'final_score': 180,
        'level_reached': 4,
        'accuracy': 0.89,
        'average_reaction_time': 320.8,
        'decisions_made': 12
    }
}
