import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch
import tempfile
import os

from models.ml_models import MentalHealthClassifier, BehaviorPredictor, AttentionAnalyzer
from models.behavior_analyzer import BehaviorAnalyzer
from models.database_models import db, User, GameSession, BehaviorData
from tests import TestHelpers

class TestMentalHealthClassifier:
    """Test cases for MentalHealthClassifier"""
    
    @pytest.fixture
    def classifier(self):
        """Create classifier instance for testing"""
        return MentalHealthClassifier()
    
    @pytest.fixture
    def sample_data(self):
        """Create sample training data"""
        return pd.DataFrame({
            'reaction_time_mean': [250, 180, 320, 200, 450],
            'reaction_time_std': [50, 30, 80, 40, 120],
            'accuracy': [0.85, 0.92, 0.78, 0.88, 0.65],
            'hesitation_frequency': [0.1, 0.05, 0.25, 0.08, 0.4],
            'stress_level_avg': [3, 2, 6, 3, 8],
            'decision_consistency': [0.8, 0.9, 0.6, 0.85, 0.4],
            # Target labels: 0=normal, 1=anxiety, 2=depression, 3=attention_deficit
            'mental_health_indicator': [0, 0, 1, 0, 2]
        })
    
    def test_classifier_initialization(self, classifier):
        """Test classifier initialization"""
        assert classifier is not None
        assert hasattr(classifier, 'model')
        assert hasattr(classifier, 'scaler')
        assert hasattr(classifier, 'feature_names')
    
    def test_feature_extraction(self, classifier, app, auth_client):
        """Test feature extraction from user data"""
        client, user = auth_client
        
        with app.app_context():
            # Create test sessions and behavior data
            for i in range(3):
                session = TestHelpers.create_test_session(user.id, 'catch_thought', score=100+i*10)
                TestHelpers.create_test_behavior_data(user.id, session.id)
            
            features = classifier.extract_features(user.id)
            
            assert isinstance(features, dict)
            assert 'reaction_time_mean' in features
            assert 'accuracy' in features
            assert 'stress_level_avg' in features
    
    def test_model_training(self, classifier, sample_data):
        """Test model training process"""
        # Prepare features and labels
        feature_cols = ['reaction_time_mean', 'reaction_time_std', 'accuracy', 
                       'hesitation_frequency', 'stress_level_avg', 'decision_consistency']
        X = sample_data[feature_cols]
        y = sample_data['mental_health_indicator']
        
        # Train model
        accuracy = classifier.train(X, y)
        
        assert accuracy is not None
        assert 0 <= accuracy <= 1
        assert classifier.model is not None
        assert classifier.scaler is not None
    
    def test_prediction(self, classifier, sample_data):
        """Test prediction functionality"""
        # Train model first
        feature_cols = ['reaction_time_mean', 'reaction_time_std', 'accuracy', 
                       'hesitation_frequency', 'stress_level_avg', 'decision_consistency']
        X = sample_data[feature_cols]
        y = sample_data['mental_health_indicator']
        classifier.train(X, y)
        
        # Test prediction
        test_features = {
            'reaction_time_mean': 300,
            'reaction_time_std': 60,
            'accuracy': 0.8,
            'hesitation_frequency': 0.15,
            'stress_level_avg': 4,
            'decision_consistency': 0.75
        }
        
        prediction = classifier.predict(test_features)
        
        assert 'class' in prediction
        assert 'confidence' in prediction
        assert 'probabilities' in prediction
        assert 0 <= prediction['confidence'] <= 1
    
    def test_model_persistence(self, classifier, sample_data):
        """Test model saving and loading"""
        # Train model
        feature_cols = ['reaction_time_mean', 'reaction_time_std', 'accuracy', 
                       'hesitation_frequency', 'stress_level_avg', 'decision_consistency']
        X = sample_data[feature_cols]
        y = sample_data['mental_health_indicator']
        classifier.train(X, y)
        
        # Save model
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pkl') as tmp:
            classifier.save_model(tmp.name)
            
            # Load model in new instance
            new_classifier = MentalHealthClassifier()
            new_classifier.load_model(tmp.name)
            
            # Test that loaded model works
            test_features = {
                'reaction_time_mean': 300,
                'reaction_time_std': 60,
                'accuracy': 0.8,
                'hesitation_frequency': 0.15,
                'stress_level_avg': 4,
                'decision_consistency': 0.75
            }
            
            original_pred = classifier.predict(test_features)
            loaded_pred = new_classifier.predict(test_features)
            
            assert original_pred['class'] == loaded_pred['class']
            
            # Cleanup
            os.unlink(tmp.name)

class TestBehaviorPredictor:
    """Test cases for BehaviorPredictor"""
    
    @pytest.fixture
    def predictor(self):
        """Create predictor instance for testing"""
        return BehaviorPredictor()
    
    def test_predictor_initialization(self, predictor):
        """Test predictor initialization"""
        assert predictor is not None
        assert hasattr(predictor, 'anxiety_model')
        assert hasattr(predictor, 'depression_model')
        assert hasattr(predictor, 'attention_model')
    
    def test_anxiety_prediction(self, predictor, app, auth_client):
        """Test anxiety indicator prediction"""
        client, user = auth_client
        
        with app.app_context():
            # Create test data indicating anxiety patterns
            for i in range(5):
                session = TestHelpers.create_test_session(user.id, 'decision_maker')
                behavior = BehaviorData(
                    user_id=user.id,
                    session_id=session.id,
                    reaction_time=400 + i*50,  # High reaction times
                    hesitation_time=150 + i*20,  # High hesitation
                    stress_level=7 + i,  # High stress
                    decision_type='avoidant_choice',
                    accuracy=False
                )
                db.session.add(behavior)
            
            db.session.commit()
            
            anxiety_indicators = predictor.predict_anxiety_indicators(user.id)
            
            assert isinstance(anxiety_indicators, dict)
            assert 'high_reaction_time_variance' in anxiety_indicators
            assert 'frequent_hesitation' in anxiety_indicators
            assert 'avoidant_choices' in anxiety_indicators
    
    def test_depression_prediction(self, predictor, app, auth_client):
        """Test depression indicator prediction"""
        client, user = auth_client
        
        with app.app_context():
            # Create test data indicating depression patterns
            for i in range(5):
                session = TestHelpers.create_test_session(user.id, 'catch_thought', score=50-i*5)  # Declining performance
                behavior = BehaviorData(
                    user_id=user.id,
                    session_id=session.id,
                    reaction_time=300,
                    stress_level=2,  # Low engagement
                    decision_type='pessimistic_choice',
                    emotional_state='sad',
                    accuracy=i < 2  # Declining accuracy
                )
                db.session.add(behavior)
            
            db.session.commit()
            
            depression_indicators = predictor.predict_depression_indicators(user.id)
            
            assert isinstance(depression_indicators, dict)
            assert 'low_engagement' in depression_indicators
            assert 'pessimistic_choices' in depression_indicators

class TestAttentionAnalyzer:
    """Test cases for AttentionAnalyzer"""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for testing"""
        return AttentionAnalyzer()
    
    def test_analyzer_initialization(self, analyzer):
        """Test analyzer initialization"""
        assert analyzer is not None
        assert hasattr(analyzer, 'attention_threshold')
        assert hasattr(analyzer, 'consistency_threshold')
    
    def test_attention_pattern_detection(self, analyzer, app, auth_client):
        """Test attention pattern detection"""
        client, user = auth_client
        
        with app.app_context():
            # Create test data with attention issues
            reaction_times = [200, 500, 180, 600, 190, 550, 175, 580]  # Inconsistent
            
            for i, rt in enumerate(reaction_times):
                session = TestHelpers.create_test_session(user.id, 'catch_thought')
                behavior = BehaviorData(
                    user_id=user.id,
                    session_id=session.id,
                    reaction_time=rt,
                    accuracy=rt < 300,  # Accuracy correlates with reaction time
                    game_level=1,
                    game_phase=f'phase_{i%3}'
                )
                db.session.add(behavior)
            
            db.session.commit()
            
            attention_patterns = analyzer.analyze_attention_patterns(user.id)
            
            assert isinstance(attention_patterns, dict)
            assert 'inconsistent_performance' in attention_patterns
            assert 'attention_lapses' in attention_patterns
    
    def test_consistency_scoring(self, analyzer):
        """Test consistency scoring algorithm"""
        # Test data with different consistency patterns
        consistent_data = [200, 210, 195, 205, 198, 202, 190, 208]
        inconsistent_data = [200, 400, 150, 500, 180, 450, 170, 520]
        
