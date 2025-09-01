import pytest
import json
from flask import url_for
from models.database_models import db, User, GameSession, BehaviorData, AnalysisReport
from tests import TestHelpers, SAMPLE_USER_DATA, SAMPLE_GAME_DATA

class TestAuthRoutes:
    """Test authentication routes"""
    
    def test_registration_page_loads(self, client):
        """Test registration page loads correctly"""
        response = client.get('/auth/register')
        assert response.status_code == 200
        assert b'Register' in response.data
    
    def test_successful_registration(self, client, app):
        """Test successful user registration"""
        with app.app_context():
            response = client.post('/auth/register', data={
                'username': 'newuser',
                'email': 'newuser@example.com',
                'password': 'TestPassword123',
                'confirm_password': 'TestPassword123',
                'age': 20,
                'gender': 'other'
            })
            
            # Should redirect to login page
            assert response.status_code == 302
            
            # Check user was created
            user = User.query.filter_by(username='newuser').first()
            assert user is not None
            assert user.email == 'newuser@example.com'
            assert user.age == 20
    
    def test_registration_validation(self, client):
        """Test registration form validation"""
        # Test password mismatch
        response = client.post('/auth/register', data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'TestPassword123',
            'confirm_password': 'DifferentPassword',
            'age': 20
        })
        assert response.status_code == 200
        assert b'Passwords do not match' in response.data
        
        # Test invalid email
        response = client.post('/auth/register', data={
            'username': 'testuser',
            'email': 'invalid-email',
            'password': 'TestPassword123',
            'confirm_password': 'TestPassword123',
            'age': 20
        })
        assert response.status_code == 200
        assert b'valid email' in response.data
        
        # Test age requirement
        response = client.post('/auth/register', data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'TestPassword123',
            'confirm_password': 'TestPassword123',
            'age': 10
        })
        assert response.status_code == 200
        assert b'at least' in response.data
    
    def test_minor_registration_consent(self, client, app):
        """Test minor registration requiring parental consent"""
        with app.app_context():
            # Register minor
            response = client.post('/auth/register', data={
                'username': 'minoruser',
                'email': 'minor@example.com',
                'password': 'TestPassword123',
                'confirm_password': 'TestPassword123',
                'age': 16,
                'gender': 'other'
            })
            
            # Should redirect to consent page
            assert response.status_code == 302
            
            # Follow redirect to consent page
            response = client.get(response.location, follow_redirects=True)
            assert b'parental consent' in response.data.lower()
    
    def test_login_success(self, client, app):
        """Test successful login"""
        with app.app_context():
            # Create user first
            user = TestHelpers.create_test_user()
            
            response = client.post('/auth/login', data={
                'username_or_email': 'testuser',
                'password': 'TestPassword123'
            })
            
            assert response.status_code == 302  # Redirect after login
    
    def test_login_failure(self, client):
        """Test login with invalid credentials"""
        response = client.post('/auth/login', data={
            'username_or_email': 'nonexistent',
            'password': 'wrongpassword'
        })
        
        assert response.status_code == 200
        assert b'Invalid username' in response.data or b'Invalid' in response.data
    
    def test_logout(self, client, app, auth_client):
        """Test user logout"""
        auth_client_obj, user = auth_client
        
        response = auth_client_obj.get('/auth/logout')
        assert response.status_code == 302  # Redirect after logout
        
        # Try to access protected page
        response = auth_client_obj.get('/dashboard/')
        assert response.status_code == 302  # Should redirect to login

class TestGameRoutes:
    """Test game-related routes"""
    
    def test_games_menu_requires_auth(self, client):
        """Test games menu requires authentication"""
        response = client.get('/games/')
        assert response.status_code == 302  # Redirect to login
    
    def test_games_menu_authenticated(self, app, auth_client):
        """Test games menu with authentication"""
        client, user = auth_client
        
        response = client.get('/games/')
        assert response.status_code == 200
        assert b'catch_thought' in response.data or b'Catch the Thought' in response.data
    
    def test_game_pages_load(self, app, auth_client):
        """Test individual game pages load"""
        client, user = auth_client
        
        game_routes = ['/games/catch_thought', '/games/stat_balance', '/games/decision_maker']
        
        for route in game_routes:
            response = client.get(route)
            assert response.status_code == 200
    
    def test_start_game_session(self, app, auth_client):
        """Test starting a game session"""
        client, user = auth_client
        
        with app.app_context():
            response = client.post('/games/start_session',
                                 json={'game_type': 'catch_thought'},
                                 content_type='application/json')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert 'session_id' in data
            
            # Check session was created in database
            session = GameSession.query.filter_by(user_id=user.id).first()
            assert session is not None
            assert session.game_type == 'catch_thought'
    
    def test_end_game_session(self, app, auth_client):
        """Test ending a game session"""
        client, user = auth_client
        
        with app.app_context():
            # Start session first
            start_response = client.post('/games/start_session',
                                       json={'game_type': 'catch_thought'},
                                       content_type='application/json')
            start_data = json.loads(start_response.data)
            session_id = start_data['session_id']
            
            # End session
            end_response = client.post('/games/end_session',
                                     json={
                                         'session_id': session_id,
                                         'final_score': 150,
                                         'completed': True,
                                         'accuracy': 0.85,
                                         'average_reaction_time': 250.5
                                     },
                                     content_type='application/json')
            
            assert end_response.status_code == 200
            end_data = json.loads(end_response.data)
            assert end_data['success'] is True
            
            # Check session was updated
            session = GameSession.query.get(session_id)
            assert session.score == 150
            assert session.completed is True
    
    def test_log_behavior_data(self, app, auth_client):
        """Test logging behavior data during gameplay"""
        client, user = auth_client
        
        with app.app_context():
            # Start session first
            start_response = client.post('/games/start_session',
                                       json={'game_type': 'decision_maker'},
                                       content_type='application/json')
            start_data = json.loads(start_response.data)
            session_id = start_data['session_id']
            
            # Log behavior data
            response = client.post('/games/log_behavior',
                                 json={
                                     'session_id': session_id,
                                     'reaction_time': 275.5,
                                     'decision_type': 'assertive_choice',
                                     'decision_value': 'politely_ask_to_stop',
                                     'stress_level': 4,
                                     'accuracy': True
                                 },
                                 content_type='application/json')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            
            # Check behavior data was stored
            behavior = BehaviorData.query.filter_by(session_id=session_id).first()
            assert behavior is not None
            assert behavior.reaction_time == 275.5
            assert behavior.decision_type == 'assertive_choice'
    
    def test_daily_game_limit(self, app, auth_client):
        """Test daily game session limit"""
        client, user = auth_client
        
        with app.app_context():
            # Mock reaching daily limit
            current_app.config['MAX_GAMES_PER_DAY'] = 2
            
            # Create 2 sessions for today
            for i in range(2):
                TestHelpers.create_test_session(user.id, 'catch_thought')
            
            # Try to start another session
            response = client.post('/games/start_session',
                                 json={'game_type': 'catch_thought'},
                                 content_type='application/json')
            
            assert response.status_code == 429  # Too Many Requests
            data = json.loads(response.data)
            assert 'limit reached' in data['error'].lower()
    
    def test_get_game_scenarios(self, app, auth_client):
        """Test getting game scenarios"""
        client, user = auth_client
        
        response = client.get('/games/get_scenarios/decision_maker')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'scenarios' in data
        assert isinstance(data['scenarios'], dict)
    
    def test_leaderboard(self, app, auth_client):
        """Test game leaderboard"""
        client, user = auth_client
        
        with app.app_context():
            # Create some completed sessions with scores
            for i in range(3):
                session = TestHelpers.create_test_session(user.id, 'catch_thought', score=100+i*50)
                session.completed = True
                db.session.commit()
            
            response = client.get('/games/leaderboard/catch_thought')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert 'leaderboard' in data
            assert 'user_best_score' in data

class TestDashboardRoutes:
    """Test dashboard routes"""
    
    def test_dashboard_requires_auth(self, client):
        """Test dashboard requires authentication"""
        response = client.get('/dashboard/')
        assert response.status_code == 302
    
    def test_dashboard_loads(self, app, auth_client):
        """Test dashboard loads for authenticated user"""
        client, user = auth_client
        
        response = client.get('/dashboard/')
        assert response.status_code == 200
        assert b'dashboard' in response.data.lower() or b'welcome' in response.data.lower()
    
    def test_progress_page(self, app, auth_client):
        """Test progress tracking page"""
        client, user = auth_client
        
        with app.app_context():
            # Create some test sessions
            for i in range(3):
                TestHelpers.create_test_session(user.id, 'catch_thought', score=100+i*25)
            
            response = client.get('/dashboard/progress')
            assert response.status_code == 200
            assert b'progress' in response.data.lower()
    
    def test_insights_insufficient_data(self, app, auth_client):
        """Test insights page with insufficient data"""
        client, user = auth_client
        
        response = client.get('/dashboard/insights', follow_redirects=True)
        # Should redirect to games if insufficient data
        assert b'complete at least' in response.data.lower() or b'insights' in response.data.lower()
    
    def test_insights_sufficient_data(self, app, auth_client):
        """Test insights page with sufficient data"""
        client, user = auth_client
        
        with app.app_context():
            # Create sufficient test data
            for i in range(5):
                session = TestHelpers.create_test_session(user.id, 'catch_thought')
                TestHelpers.create_test_behavior_data(user.id, session.id)
            
            response = client.get('/dashboard/insights')
            assert response.status_code == 200 or response.status_code == 302  # May redirect if no analysis yet

class TestAnalysisRoutes:
    """Test analysis routes"""
    
    def test_analysis_index_insufficient_data(self, app, auth_client):
        """Test analysis index with insufficient data"""
        client, user = auth_client
        
        response = client.get('/analysis/', follow_redirects=True)
        assert response.status_code == 200
        # Should show message about needing more sessions
    
    def test_generate_analysis_insufficient_data(self, app, auth_client):
        """Test analysis generation with insufficient data"""
        client, user = auth_client
        
        response = client.post('/analysis/generate',
                             json={'days_back': 30},
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'insufficient' in data['error'].lower()
    
    def test_generate_analysis_sufficient_data(self, app, auth_client):
        """Test analysis generation with sufficient data"""
        client, user = auth_client
        
        with app.app_context():
            # Create sufficient test data
            for i in range(5):
                session = TestHelpers.create_test_session(user.id, 'catch_thought')
                TestHelpers.create_test_behavior_data(user.id, session.id)
            
            # Mock the analysis generation to avoid ML complexity in tests
            with patch('models.behavior_analyzer.BehaviorAnalyzer.generate_comprehensive_report') as mock_generate:
                mock_report = AnalysisReport(
                    user_id=user.id,
                    report_type='personal',
                    sessions_analyzed=5,
                    insights={'test': 'data'},
                    overall_wellbeing_score=0.75
                )
                db.session.add(mock_report)
                db.session.commit()
                
                mock_generate.return_value = mock_report
                
                response = client.post('/analysis/generate',
                                     json={'days_back': 30},
                                     content_type='application/json')
                
                assert response.status_code == 200
                data = json.loads(response.data)
                assert data['success'] is True
    
    def test_view_report(self, app, auth_client):
        """Test viewing analysis report"""
        client, user = auth_client
        
        with app.app_context():
            # Create test report
            report = AnalysisReport(
                user_id=user.id,
                report_type='personal',
                sessions_analyzed=5,
                insights={'anxiety': {'score': 0.3}, 'depression': {'score': 0.2}},
                overall_wellbeing_score=0.75,
                summary='Test report summary'
            )
            db.session.add(report)
            db.session.commit()
            
            response = client.get(f'/analysis/report/{report.id}')
            assert response.status_code == 200
    
    def test_api_activity_data(self, app, auth_client):
        """Test activity data API endpoint"""
        client, user = auth_client
        
        with app.app_context():
            # Create test session
            TestHelpers.create_test_session(user.id, 'catch_thought')
            
            response = client.get('/dashboard/api/activity_data?days=7')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert isinstance(data, list)
    
    def test_api_performance_data(self, app, auth_client):
        """Test performance data API endpoint"""
        client, user = auth_client
        
        response = client.get('/dashboard/api/performance_data?game_type=all')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert isinstance(data, list)

class TestErrorHandling:
    """Test error handling across routes"""
    
    def test_404_error(self, client):
        """Test 404 error handling"""
        response = client.get('/nonexistent-page')
        assert response.status_code == 404
    
    def test_invalid_json_request(self, app, auth_client):
        """Test handling of invalid JSON in API requests"""
        client, user = auth_client
        
        response = client.post('/games/start_session',
                             data='invalid json',
                             content_type='application/json')
        
        assert response.status_code == 400 or response.status_code == 500
    
    def test_unauthorized_access(self, client, app):
        """Test unauthorized access to protected routes"""
        protected_routes = [
            '/dashboard/',
            '/games/',
            '/analysis/',
            '/auth/profile'
        ]
        
        for route in protected_routes:
            response = client.get(route)
            assert response.status_code == 302  # Redirect to login
    
    def test_access_other_user_data(self, app, auth_client):
        """Test that users cannot access other users' data"""
        client, user1 = auth_client
        
        with app.app_context():
            # Create another user and their report
            user2 = TestHelpers.create_test_user('otheruser', 'other@example.com')
            report2 = AnalysisReport(
                user_id=user2.id,
                report_type='personal',
                sessions_analyzed=3,
                insights={'test': 'data'}
            )
            db.session.add(report2)
            db.session.commit()
            
            # Try to access other user's report
            response = client.get(f'/analysis/report/{report2.id}')
            assert response.status_code == 404  # Should not be found

# Import patch for mocking
from unittest.mock import patch
