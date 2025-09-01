import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from models.database_models import db, GameSession, BehaviorData
from tests import TestHelpers, SAMPLE_GAME_DATA

class TestCatchTheThoughtGame:
    """Test cases for Catch the Thought game functionality"""
    
    def test_game_initialization(self, app, auth_client):
        """Test game initialization and setup"""
        client, user = auth_client
        
        with app.app_context():
            # Start session
            response = client.post('/games/start_session',
                                 json={'game_type': 'catch_thought'},
                                 content_type='application/json')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            session_id = data['session_id']
            
            # Check session was created properly
            session = GameSession.query.get(session_id)
            assert session.game_type == 'catch_thought'
            assert session.user_id == user.id
            assert session.started_at is not None
    
    def test_thought_catching_mechanics(self, app, auth_client):
        """Test thought catching game mechanics"""
        client, user = auth_client
        
        with app.app_context():
            # Start session
            start_response = client.post('/games/start_session',
                                       json={'game_type': 'catch_thought'},
                                       content_type='application/json')
            session_id = json.loads(start_response.data)['session_id']
            
            # Simulate catching positive thoughts (good)
            for i in range(3):
                response = client.post('/games/log_behavior',
                                     json={
                                         'session_id': session_id,
                                         'reaction_time': 200 + i*10,
                                         'decision_type': 'positive_catch',
                                         'decision_value': 'caught_positive_thought',
                                         'accuracy': True,
                                         'emotional_state': 'focused',
                                         'game_level': 1,
                                         'game_phase': 'catching'
                                     },
                                     content_type='application/json')
                assert response.status_code == 200
            
            # Simulate missing negative thoughts (bad)
            for i in range(2):
                response = client.post('/games/log_behavior',
                                     json={
                                         'session_id': session_id,
                                         'reaction_time': 400 + i*50,
                                         'decision_type': 'negative_miss',
                                         'decision_value': 'missed_negative_thought',
                                         'accuracy': False,
                                         'emotional_state': 'distracted',
                                         'game_level': 1,
                                         'game_phase': 'catching'
                                     },
                                     content_type='application/json')
                assert response.status_code == 200
            
            # Check behavior data was logged
            behavior_count = BehaviorData.query.filter_by(session_id=session_id).count()
            assert behavior_count == 5
    
    def test_thought_categorization(self, app, auth_client):
        """Test thought categorization accuracy"""
        client, user = auth_client
        
        # Get thought scenarios
        response = client.get('/games/get_scenarios/catch_thought')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        scenarios = data['scenarios']
        
        assert 'positive_thoughts' in scenarios
        assert 'negative_thoughts' in scenarios
        assert 'neutral_thoughts' in scenarios
        
        # Verify thought categorization
        assert len(scenarios['positive_thoughts']) > 0
        assert len(scenarios['negative_thoughts']) > 0
        assert len(scenarios['neutral_thoughts']) > 0
    
    def test_performance_tracking(self, app, auth_client):
        """Test performance tracking in catch the thought"""
        client, user = auth_client
        
        with app.app_context():
            start_response = client.post('/games/start_session',
                                       json={'game_type': 'catch_thought'},
                                       content_type='application/json')
            session_id = json.loads(start_response.data)['session_id']
            
            # Simulate varied performance
            performance_data = [
                {'reaction_time': 180, 'accuracy': True, 'thought_type': 'positive'},
                {'reaction_time': 220, 'accuracy': True, 'thought_type': 'negative'},
                {'reaction_time': 450, 'accuracy': False, 'thought_type': 'positive'},
                {'reaction_time': 190, 'accuracy': True, 'thought_type': 'neutral'},
            ]
            
            for data_point in performance_data:
                client.post('/games/log_behavior',
                          json={
                              'session_id': session_id,
                              'reaction_time': data_point['reaction_time'],
                              'accuracy': data_point['accuracy'],
                              'decision_type': f"{data_point['thought_type']}_thought",
                              'game_level': 1
                          },
                          content_type='application/json')
            
            # End session with calculated metrics
            avg_reaction_time = sum(d['reaction_time'] for d in performance_data) / len(performance_data)
            accuracy = sum(1 for d in performance_data if d['accuracy']) / len(performance_data)
            
            end_response = client.post('/games/end_session',
                                     json={
                                         'session_id': session_id,
                                         'final_score': 120,
                                         'accuracy': accuracy,
                                         'average_reaction_time': avg_reaction_time,
                                         'completed': True
                                     },
                                     content_type='application/json')
            
            assert end_response.status_code == 200
            
            # Verify session data
            session = GameSession.query.get(session_id)
            assert session.accuracy == accuracy
            assert abs(session.average_reaction_time - avg_reaction_time) < 1.0

class TestStatBalanceGame:
    """Test cases for Stat Balance game functionality"""
    
    def test_stat_balancing_scenarios(self, app, auth_client):
        """Test stat balancing game scenarios"""
        client, user = auth_client
        
        response = client.get('/games/get_scenarios/stat_balance')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        scenarios = data['scenarios']['situations']
        
        # Verify scenario structure
        for scenario in scenarios:
            assert 'title' in scenario
            assert 'description' in scenario
            assert 'stats' in scenario
            assert len(scenario['stats']) >= 3  # Should have multiple stats to balance
    
    def test_stat_allocation_decisions(self, app, auth_client):
        """Test stat allocation decision making"""
        client, user = auth_client
        
        with app.app_context():
            start_response = client.post('/games/start_session',
                                       json={'game_type': 'stat_balance'},
                                       content_type='application/json')
            session_id = json.loads(start_response.data)['session_id']
            
            # Simulate stat allocation decisions
            allocation_decisions = [
                {'social_energy': 7, 'anxiety': 3, 'confidence': 8, 'fun': 6},
                {'study_time': 9, 'stress': 6, 'sleep': 4, 'confidence': 7},
                {'personal_time': 5, 'friendship': 9, 'stress': 4, 'guilt': 3}
            ]
            
            for i, allocation in enumerate(allocation_decisions):
                response = client.post('/games/log_behavior',
                                     json={
                                         'session_id': session_id,
                                         'decision_type': 'stat_allocation',
                                         'decision_value': json.dumps(allocation),
                                         'reaction_time': 2000 + i*500,  # Longer thinking time
                                         'game_level': i + 1,
                                         'game_phase': f'scenario_{i+1}',
                                         'metadata': {'allocation': allocation}
                                     },
                                     content_type='application/json')
                assert response.status_code == 200
            
            # End session
            end_response = client.post('/games/end_session',
                                     json={
                                         'session_id': session_id,
                                         'final_score': 180,
                                         'level_reached': 3,
                                         'decisions_made': len(allocation_decisions),
                                         'completed': True
                                     },
                                     content_type='application/json')
            
            assert end_response.status_code == 200
            
            # Verify decisions were logged
            behavior_count = BehaviorData.query.filter_by(
                session_id=session_id,
                decision_type='stat_allocation'
            ).count()
            assert behavior_count == 3
    
    def test_balance_optimization_analysis(self, app, auth_client):
        """Test analysis of balance optimization patterns"""
        client, user = auth_client
        
        with app.app_context():
            start_response = client.post('/games/start_session',
                                       json={'game_type': 'stat_balance'},
                                       content_type='application/json')
            session_id = json.loads(start_response.data)['session_id']
            
            # Simulate different balancing strategies
            strategies = [
                'balanced',     # Even distribution
                'risk_averse',  # Conservative choices
                'aggressive',   # High-risk, high-reward
                'reactive'      # Based on immediate needs
            ]
            
            for i, strategy in enumerate(strategies):
                response = client.post('/games/log_behavior',
                                     json={
                                         'session_id': session_id,
                                         'decision_type': 'balancing_strategy',
                                         'decision_value': strategy,
                                         'game_level': i + 1,
                                         'confidence_level': 0.7 if strategy == 'balanced' else 0.5,
                                         'hesitation_time': 100 if strategy == 'aggressive' else 300
                                     },
                                     content_type='application/json')
                assert response.status_code == 200
            
            # Check strategy diversity was captured
            strategies_logged = BehaviorData.query.filter_by(
                session_id=session_id,
                decision_type='balancing_strategy'
            ).all()
            
            strategy_values = [s.decision_value for s in strategies_logged]
            assert len(set(strategy_values)) == 4  # All unique strategies

class TestDecisionMakerGame:
    """Test cases for Decision Maker game functionality"""
    
    def test_decision_scenarios(self, app, auth_client):
        """Test decision maker game scenarios"""
        client, user = auth_client
        
        response = client.get('/games/get_scenarios/decision_maker')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        scenarios = data['scenarios']['scenarios']
        
        # Verify scenario structure
        for scenario in scenarios:
            assert 'id' in scenario
            assert 'situation' in scenario
            assert 'options' in scenario
            assert len(scenario['options']) >= 3  # Multiple choice options
            
            for option in scenario['options']:
                assert 'text' in option
                assert 'type' in option  # Decision type classification
    
    def test_decision_pattern_analysis(self, app, auth_client):
        """Test analysis of decision making patterns"""
        client, user = auth_client
        
        with app.app_context():
            start_response = client.post('/games/start_session',
                                       json={'game_type': 'decision_maker'},
                                       content_type='application/json')
            session_id = json.loads(start_response.data)['session_id']
            
            # Simulate decision patterns
            decision_patterns = [
                {'type': 'assertive', 'reaction_time': 200, 'confidence': 0.8},
                {'type': 'avoidant', 'reaction_time': 450, 'confidence': 0.4},
                {'type': 'aggressive', 'reaction_time': 150, 'confidence': 0.9},
                {'type': 'passive_aggressive', 'reaction_time': 300, 'confidence': 0.6},
                {'type': 'assertive', 'reaction_time': 180, 'confidence': 0.85}
            ]
            
            for i, pattern in enumerate(decision_patterns):
                response = client.post('/games/log_behavior',
                                     json={
                                         'session_id': session_id,
                                         'decision_type': pattern['type'],
                                         'reaction_time': pattern['reaction_time'],
                                         'confidence_level': pattern['confidence'],
                                         'game_level': (i // 2) + 1,
                                         'accuracy': pattern['type'] in ['assertive', 'practical']
                                     },
                                     content_type='application/json')
                assert response.status_code == 200
            
            # Analyze decision patterns
            decisions = BehaviorData.query.filter_by(session_id=session_id).all()
            
            # Count assertive decisions (positive indicator)
            assertive_count = sum(1 for d in decisions if d.decision_type == 'assertive')
            avoidant_count = sum(1 for d in decisions if d.decision_type == 'avoidant')
            
            assert assertive_count == 2
            assert avoidant_count == 1
    
    def test_social_scenario_responses(self, app, auth_client):
        """Test responses to social scenarios"""
        client, user = auth_client
        
        with app.app_context():
            start_response = client.post('/games/start_session',
                                       json={'game_type': 'decision_maker'},
                                       content_type='application/json')
            session_id = json.loads(start_response.data)['session_id']
            
            # Test specific social scenarios
            social_scenarios = [
                {
                    'scenario': 'confrontation',
                    'response': 'direct_communication',
                    'stress_induced': 6,
                    'reaction_time': 2500
                },
                {
                    'scenario': 'peer_pressure',
                    'response': 'boundary_setting',
                    'stress_induced': 4,
                    'reaction_time': 1800
                },
                {
                    'scenario': 'helping_others',
                    'response': 'empathetic_support',
                    'stress_induced': 2,
                    'reaction_time': 1200
                }
            ]
            
            for scenario_data in social_scenarios:
                response = client.post('/games/log_behavior',
                                     json={
                                         'session_id': session_id,
                                         'decision_type': 'social_scenario',
                                         'decision_value': scenario_data['response'],
                                         'stress_level': scenario_data['stress_induced'],
                                         'reaction_time': scenario_data['reaction_time'],
                                         'metadata': {'scenario_type': scenario_data['scenario']}
                                     },
                                     content_type='application/json')
                assert response.status_code == 200
            
            # Verify stress patterns were captured
            behaviors = BehaviorData.query.filter_by(session_id=session_id).all()
            stress_levels = [b.stress_level for b in behaviors]
            
            # Confrontation should induce highest stress
            assert max(stress_levels) == 6
            # Helping others should induce lowest stress
            assert min(stress_levels) == 2

class TestGameIntegration:
    """Integration tests for game systems"""
    
    def test_cross_game_performance_tracking(self, app, auth_client):
        """Test performance tracking across different games"""
        client, user = auth_client
        
        with app.app_context():
            game_sessions = []
            
            # Play each game type
            for game_type in ['catch_thought', 'stat_balance', 'decision_maker']:
                start_response = client.post('/games/start_session',
                                           json={'game_type': game_type},
                                           content_type='application/json')
                session_id = json.loads(start_response.data)['session_id']
                
                # Log some behavior data
                client.post('/games/log_behavior',
                          json={
                              'session_id': session_id,
                              'reaction_time': 250,
                              'accuracy': True,
                              'decision_type': f'{game_type}_decision'
                          },
                          content_type='application/json')
                
                # End session
                end_response = client.post('/games/end_session',
                                         json={
                                             'session_id': session_id,
                                             'final_score': 150,
                                             'completed': True,
                                             'accuracy': 0.85
                                         },
                                         content_type='application/json')
                
                game_sessions.append(session_id)
                assert end_response.status_code == 200
            
            # Verify all sessions were created
            total_sessions = GameSession.query.filter_by(user_id=user.id).count()
            assert total_sessions == 3
            
            # Check cross-game data consistency
            sessions = GameSession.query.filter_by(user_id=user.id).all()
            for session in sessions:
                assert session.score == 150
                assert session.accuracy == 0.85
                assert session.completed is True
    
    def test_game_session_persistence(self, app, auth_client):
        """Test game session data persistence"""
        client, user = auth_client
        
        with app.app_context():
            # Start session
            start_response = client.post('/games/start_session',
                                       json={'game_type': 'catch_thought'},
                                       content_type='application/json')
            session_id = json.loads(start_response.data)['session_id']
            
            # Add comprehensive behavioral data
            behavior_entries = [
                {
                    'reaction_time': 225,
                    'decision_type': 'positive_catch',
                    'accuracy': True,
                    'stress_level': 3,
                    'emotional_state': 'focused'
                },
                {
                    'reaction_time': 180,
                    'decision_type': 'negative_catch',
                    'accuracy': True,
                    'stress_level': 2,
                    'emotional_state': 'calm'
                },
                {
                    'reaction_time': 350,
                    'decision_type': 'neutral_miss',
                    'accuracy': False,
                    'stress_level': 5,
                    'emotional_state': 'distracted'
                }
            ]
            
            for entry in behavior_entries:
                client.post('/games/log_behavior',
                          json=dict({'session_id': session_id}, **entry),
                          content_type='application/json')
            
            # End session with detailed metrics
            end_response = client.post('/games/end_session',
                                     json={
                                         'session_id': session_id,
                                         'final_score': 175,
                                         'level_reached': 3,
                                         'accuracy': 0.67,
                                         'average_reaction_time': 251.7,
                                         'consistency_score': 0.75,
                                         'decisions_made': 3,
                                         'completed': True
                                     },
                                     content_type='application/json')
            
            assert end_response.status_code == 200
            
            # Verify complete data persistence
            session = GameSession.query.get(session_id)
            assert session.score == 175
            assert session.level_reached == 3
            assert session.accuracy == 0.67
            assert session.decisions_made == 3
            
            # Verify behavior data persistence
            behaviors = BehaviorData.query.filter_by(session_id=session_id).all()
            assert len(behaviors) == 3
            
            # Verify specific behavior data
            positive_catch = next((b for b in behaviors if b.decision_type == 'positive_catch'), None)
            assert positive_catch is not None
            assert positive_catch.reaction_time == 225
            assert positive_catch.emotional_state == 'focused'
    
    def test_game_feedback_system(self, app, auth_client):
        """Test game feedback and rating system"""
        client, user = auth_client
        
        with app.app_context():
            # Complete a game session
            start_response = client.post('/games/start_session',
                                       json={'game_type': 'stat_balance'},
                                       content_type='application/json')
            session_id = json.loads(start_response.data)['session_id']
            
            # End session
            client.post('/games/end_session',
                       json={
                           'session_id': session_id,
                           'final_score': 200,
                           'completed': True
                       },
                       content_type='application/json')
            
            # Submit feedback
            feedback_response = client.post('/games/game_feedback',
                                          json={
                                              'session_id': session_id,
                                              'enjoyment_rating': 4,
                                              'difficulty_rating': 3,
                                              'engagement_level': 5,
                                              'comments': 'Great game! Really engaging.',
                                              'would_play_again': True
                                          },
                                          content_type='application/json')
            
            assert feedback_response.status_code == 200
            
            # Verify feedback was stored
            session = GameSession.query.get(session_id)
            assert 'user_feedback' in session.behavioral_data
            
            feedback_data = session.behavioral_data['user_feedback']
            assert feedback_data['enjoyment_rating'] == 4
            assert feedback_data['would_play_again'] is True
    
    def test_pause_resume_functionality(self, app, auth_client):
        """Test game pause and resume functionality"""
        client, user = auth_client
        
        with app.app_context():
            # Start session
            start_response = client.post('/games/start_session',
                                       json={'game_type': 'decision_maker'},
                                       content_type='application/json')
            session_id = json.loads(start_response.data)['session_id']
            
            # Play for a while
            client.post('/games/log_behavior',
                       json={
                           'session_id': session_id,
                           'reaction_time': 200,
                           'decision_type': 'assertive'
                       },
                       content_type='application/json')
            
            # Pause game
            pause_response = client.post('/games/pause_session',
                                       json={
                                           'session_id': session_id,
                                           'current_score': 75,
                                           'current_level': 2,
                                           'time_played': 120
                                       },
                                       content_type='application/json')
            
            assert pause_response.status_code == 200
            
            # Resume game
            resume_response = client.post('/games/resume_session',
                                        json={'session_id': session_id},
                                        content_type='application/json')
            
            assert resume_response.status_code == 200
            resume_data = json.loads(resume_response.data)
            assert 'pause_data' in resume_data
            assert resume_data['pause_data']['current_score'] == 75
