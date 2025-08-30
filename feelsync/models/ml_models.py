import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib
import json
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class BehaviorPredictor:
    """Main ML model for predicting behavioral patterns and mental health indicators"""
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.feature_names = [
            'reaction_time_avg', 'reaction_time_std', 'accuracy', 'hesitation_count',
            'error_rate', 'decision_time_avg', 'emotional_choice_bias', 'consistency_score',
            'impulsivity_indicators', 'attention_lapses', 'stress_markers'
        ]
        self.initialize_models()
    
    def initialize_models(self):
        """Initialize all ML models"""
        
        # Anxiety Detection Model
        self.models['anxiety'] = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            min_samples_split=5,
            min_samples_leaf=2
        )
        
        # Depression Detection Model
        self.models['depression'] = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            min_samples_split=5,
            min_samples_leaf=2
        )
        
        # Attention/ADHD Detection Model
        self.models['attention'] = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            min_samples_split=5,
            min_samples_leaf=2
        )
        
        # Behavioral Cluster Classification
        self.models['cluster'] = KMeans(
            n_clusters=3,
            random_state=42,
            n_init=10
        )
        
        # Overall Risk Assessment
        self.models['risk'] = LogisticRegression(
            random_state=42,
            max_iter=1000
        )
        
        # Decision Tree for Interpretable Rules
        self.models['decision_tree'] = DecisionTreeClassifier(
            max_depth=6,
            min_samples_split=10,
            random_state=42
        )
        
        # Initialize scalers
        for model_name in ['anxiety', 'depression', 'attention', 'cluster', 'risk']:
            self.scalers[model_name] = StandardScaler()
    
    def extract_features(self, behavioral_data):
        """Extract ML features from behavioral data"""
        
        if isinstance(behavioral_data, str):
            behavioral_data = json.loads(behavioral_data)
        
        # Initialize feature vector
        features = np.zeros(len(self.feature_names))
        
        try:
            # Reaction time features
            reaction_times = behavioral_data.get('reactionTimes', [])
            if reaction_times:
                features[0] = np.mean(reaction_times)  # reaction_time_avg
                features[1] = np.std(reaction_times)   # reaction_time_std
            
            # Accuracy
            features[2] = behavioral_data.get('accuracy', 0) / 100.0
            
            # Hesitation count
            hesitation_times = behavioral_data.get('hesitationTimes', [])
            features[3] = len(hesitation_times)
            
            # Error rate
            total_clicks = behavioral_data.get('totalClicks', 1)
            mistakes = behavioral_data.get('mistakes', 0)
            features[4] = mistakes / max(total_clicks, 1)
            
            # Decision time average
            decision_times = behavioral_data.get('decisionTimes', [])
            if decision_times:
                features[5] = np.mean(decision_times)
            
            # Emotional choice bias
            emotional_choices = behavioral_data.get('emotionalChoices', {})
            total_emotional = sum(emotional_choices.values())
            if total_emotional > 0:
                negative_ratio = emotional_choices.get('negative', 0) / total_emotional
                positive_ratio = emotional_choices.get('positive', 0) / total_emotional
                features[6] = negative_ratio - positive_ratio  # Bias towards negative
            
            # Consistency score (inverse of standard deviation)
            if reaction_times and len(reaction_times) > 1:
                features[7] = 1 / (1 + np.std(reaction_times) / np.mean(reaction_times))
            
            # Impulsivity indicators (fast reactions with high error rate)
            fast_reactions = [rt for rt in reaction_times if rt < 500]  # < 500ms
            features[8] = len(fast_reactions) / max(len(reaction_times), 1)
            
            # Attention lapses (very slow reactions)
            slow_reactions = [rt for rt in reaction_times if rt > 2000]  # > 2s
            features[9] = len(slow_reactions) / max(len(reaction_times), 1)
            
            # Stress markers (combination of high error rate and high reaction time variance)
            if reaction_times:
                stress_score = features[4] * features[1] / 1000  # Normalized stress indicator
                features[10] = min(stress_score, 1.0)
            
        except Exception as e:
            print(f"Feature extraction error: {e}")
            # Return default features if extraction fails
            pass
        
        return features
    
    def predict_anxiety(self, behavioral_data):
        """Predict anxiety indicators from behavioral data"""
        features = self.extract_features(behavioral_data)
        
        # Rule-based fallback if model not trained
        if not hasattr(self.models['anxiety'], 'feature_importances_'):
            return self._rule_based_anxiety_prediction(features)
        
        features_scaled = self.scalers['anxiety'].transform([features])
        anxiety_score = self.models['anxiety'].predict(features_scaled)[0]
        
        return max(0, min(100, anxiety_score))
    
    def predict_depression(self, behavioral_data):
        """Predict depression indicators from behavioral data"""
        features = self.extract_features(behavioral_data)
        
        # Rule-based fallback if model not trained
        if not hasattr(self.models['depression'], 'feature_importances_'):
            return self._rule_based_depression_prediction(features)
        
        features_scaled = self.scalers['depression'].transform([features])
        depression_score = self.models['depression'].predict(features_scaled)[0]
        
        return max(0, min(100, depression_score))
    
    def predict_attention(self, behavioral_data):
        """Predict attention/ADHD indicators from behavioral data"""
        features = self.extract_features(behavioral_data)
        
        # Rule-based fallback if model not trained
        if not hasattr(self.models['attention'], 'feature_importances_'):
            return self._rule_based_attention_prediction(features)
        
        features_scaled = self.scalers['attention'].transform([features])
        attention_score = self.models['attention'].predict(features_scaled)[0]
        
        return max(0, min(100, attention_score))
    
    def predict_cluster(self, behavioral_data):
        """Predict behavioral cluster"""
        features = self.extract_features(behavioral_data)
        
        # Rule-based clustering if model not trained
        if not hasattr(self.models['cluster'], 'cluster_centers_'):
            return self._rule_based_clustering(features)
        
        features_scaled = self.scalers['cluster'].transform([features])
        cluster = self.models['cluster'].predict(features_scaled)[0]
        
        cluster_names = ['fast_accurate', 'slow_consistent', 'erratic']
        return cluster_names[cluster]
    
    def _rule_based_anxiety_prediction(self, features):
        """Rule-based anxiety prediction fallback"""
        reaction_time_avg, reaction_time_std, accuracy, hesitation_count, error_rate, _, emotional_bias, consistency, _, _, stress_markers = features
        
        anxiety_score = 0
        
        # High reaction time variance suggests anxiety
        if reaction_time_std > 500:
            anxiety_score += 30
        
        # High hesitation count
        anxiety_score += min(hesitation_count * 5, 25)
        
        # Low accuracy due to overthinking
        if accuracy < 0.7:
            anxiety_score += 20
        
        # Negative emotional bias
        if emotional_bias > 0.2:
            anxiety_score += 15
        
        # Stress markers
        anxiety_score += stress_markers * 30
        
        return min(anxiety_score, 100)
    
    def _rule_based_depression_prediction(self, features):
        """Rule-based depression prediction fallback"""
        reaction_time_avg, reaction_time_std, accuracy, hesitation_count, error_rate, decision_time_avg, emotional_bias, consistency, _, attention_lapses, _ = features
        
        depression_score = 0
        
        # Slow reaction times
        if reaction_time_avg > 1000:
            depression_score += 25
        
        # High number of attention lapses
        depression_score += attention_lapses * 40
        
        # Negative emotional bias
        if emotional_bias > 0.3:
            depression_score += 30
        
        # Low consistency (lack of engagement)
        if consistency < 0.5:
            depression_score += 20
        
        # Slow decision making
        if decision_time_avg > 2000:
            depression_score += 15
        
        return min(depression_score, 100)
    
    def _rule_based_attention_prediction(self, features):
        """Rule-based attention/ADHD prediction fallback"""
        reaction_time_avg, reaction_time_std, accuracy, hesitation_count, error_rate, _, _, consistency, impulsivity, attention_lapses, _ = features
        
        attention_score = 100  # Start with perfect attention, subtract issues
        
        # High impulsivity reduces attention score
        attention_score -= impulsivity * 40
        
        # Attention lapses
        attention_score -= attention_lapses * 50
        
        # High reaction time variance (inconsistency)
        if reaction_time_std > 600:
            attention_score -= 30
        
        # High error rate
        attention_score -= error_rate * 40
        
        # Low consistency
        attention_score -= (1 - consistency) * 20
        
        return max(0, attention_score)
    
    def _rule_based_clustering(self, features):
        """Rule-based clustering fallback"""
        reaction_time_avg, reaction_time_std, accuracy, hesitation_count, error_rate, _, _, consistency, impulsivity, attention_lapses, _ = features
        
        # Fast and accurate cluster
        if reaction_time_avg < 800 and accuracy > 0.8 and error_rate < 0.2:
            return 'fast_accurate'
        
        # Slow but consistent cluster
        elif reaction_time_avg > 1200 and consistency > 0.7 and error_rate < 0.3:
            return 'slow_consistent'
        
        # Erratic cluster (default)
        else:
            return 'erratic'
    
    def train_models(self, training_data):
        """Train all models with provided data"""
        if len(training_data) < 10:
            print("Insufficient training data. Using rule-based predictions.")
            return
        
        # Prepare features and targets
        X = []
        y_anxiety = []
        y_depression = []
        y_attention = []
        y_clusters = []
        
        for data_point in training_data:
            features = self.extract_features(data_point['behavioral_data'])
            X.append(features)
            y_anxiety.append(data_point.get('anxiety_score', 0))
            y_depression.append(data_point.get('depression_score', 0))
            y_attention.append(data_point.get('attention_score', 50))
            y_clusters.append(data_point.get('cluster', 'erratic'))
        
        X = np.array(X)
        
        # Train regression models
        for model_name, y_values in [
            ('anxiety', y_anxiety),
            ('depression', y_depression),
            ('attention', y_attention)
        ]:
            if len(set(y_values)) > 1:  # Check if there's variance in target
                X_scaled = self.scalers[model_name].fit_transform(X)
                self.models[model_name].fit(X_scaled, y_values)
        
        # Train clustering model
        X_scaled = self.scalers['cluster'].fit_transform(X)
        self.models['cluster'].fit(X_scaled)
        
        # Train risk classification model
        risk_labels = ['low' if max(y_anxiety[i], y_depression[i]) < 50 else 'high' 
                      for i in range(len(y_anxiety))]
        if len(set(risk_labels)) > 1:
            X_scaled = self.scalers['risk'].fit_transform(X)
            self.models['risk'].fit(X_scaled, risk_labels)
    
    def save_models(self, model_dir='models/trained'):
        """Save trained models to disk"""
        os.makedirs(model_dir, exist_ok=True)
        
        for model_name, model in self.models.items():
            model_path = os.path.join(model_dir, f'{model_name}_model.pkl')
            joblib.dump(model, model_path)
            
            scaler_path = os.path.join(model_dir, f'{model_name}_scaler.pkl')
            if model_name in self.scalers:
                joblib.dump(self.scalers[model_name], scaler_path)
    
    def load_models(self, model_dir='models/trained'):
        """Load trained models from disk"""
        try:
            for model_name in self.models.keys():
                model_path = os.path.join(model_dir, f'{model_name}_model.pkl')
                if os.path.exists(model_path):
                    self.models[model_name] = joblib.load(model_path)
                
                scaler_path = os.path.join(model_dir, f'{model_name}_scaler.pkl')
                if os.path.exists(scaler_path) and model_name in self.scalers:
                    self.scalers[model_name] = joblib.load(scaler_path)
        except Exception as e:
            print(f"Error loading models: {e}")
    
    def get_feature_importance(self):
        """Get feature importance from trained models"""
        importance_data = {}
        
        for model_name in ['anxiety', 'depression', 'attention']:
            model = self.models[model_name]
            if hasattr(model, 'feature_importances_'):
                importance_data[model_name] = dict(zip(
                    self.feature_names,
                    model.feature_importances_
                ))
        
        return importance_data

class ReportMLAnalyzer:
    """Specialized ML analyzer for generating comprehensive reports"""
    
    def __init__(self):
        self.predictor = BehaviorPredictor()
    
    def analyze_user_patterns(self, user_sessions):
        """Analyze patterns across multiple user sessions"""
        if not user_sessions:
            return self._default_analysis()
        
        session_analyses = []
        for session in user_sessions:
            behavioral_data = json.loads(session.game_data) if session.game_data else {}
            
            analysis = {
                'session_id': session.id,
                'game_type': session.game_type,
                'date': session.created_at,
                'anxiety_score': self.predictor.predict_anxiety(behavioral_data),
                'depression_score': self.predictor.predict_depression(behavioral_data),
                'attention_score': self.predictor.predict_attention(behavioral_data),
                'cluster': self.predictor.predict_cluster(behavioral_data),
                'features': self.predictor.extract_features(behavioral_data)
            }
            session_analyses.append(analysis)
        
        return self._generate_trend_analysis(session_analyses)
    
    def _generate_trend_analysis(self, session_analyses):
        """Generate trend analysis from multiple sessions"""
        if not session_analyses:
            return self._default_analysis()
        
        # Calculate trends
        anxiety_scores = [s['anxiety_score'] for s in session_analyses]
        depression_scores = [s['depression_score'] for s in session_analyses]
        attention_scores = [s['attention_score'] for s in session_analyses]
        
        trends = {
            'anxiety_trend': self._calculate_trend(anxiety_scores),
            'depression_trend': self._calculate_trend(depression_scores),
            'attention_trend': self._calculate_trend(attention_scores),
            'most_recent_scores': {
                'anxiety': anxiety_scores[-1] if anxiety_scores else 0,
                'depression': depression_scores[-1] if depression_scores else 0,
                'attention': attention_scores[-1] if attention_scores else 50
            },
            'average_scores': {
                'anxiety': np.mean(anxiety_scores) if anxiety_scores else 0,
                'depression': np.mean(depression_scores) if depression_scores else 0,
                'attention': np.mean(attention_scores) if attention_scores else 50
            },
            'session_count': len(session_analyses),
            'improvement_indicators': self._identify_improvements(session_analyses)
        }
        
        return trends
    
    def _calculate_trend(self, scores):
        """Calculate trend direction for a series of scores"""
        if len(scores) < 2:
            return 'stable'
        
        recent_avg = np.mean(scores[-3:]) if len(scores) >= 3 else scores[-1]
        earlier_avg = np.mean(scores[:-3]) if len(scores) >= 6 else scores[0]
        
        diff = recent_avg - earlier_avg
        
        if diff > 10:
            return 'increasing'
        elif diff < -10:
            return 'decreasing'
        else:
            return 'stable'
    
    def _identify_improvements(self, session_analyses):
        """Identify positive improvements in user behavior"""
        improvements = []
        
        if len(session_analyses) < 2:
            return improvements
        
        first_half = session_analyses[:len(session_analyses)//2]
        second_half = session_analyses[len(session_analyses)//2:]
        
        # Check for accuracy improvements
        first_avg_accuracy = np.mean([s['features'][2] for s in first_half])
        second_avg_accuracy = np.mean([s['features'][2] for s in second_half])
        
        if second_avg_accuracy > first_avg_accuracy + 0.1:
            improvements.append("Significant improvement in accuracy")
        
        # Check for reaction time consistency
        first_rt_std = np.mean([s['features'][1] for s in first_half])
        second_rt_std = np.mean([s['features'][1] for s in second_half])
        
        if second_rt_std < first_rt_std * 0.8:
            improvements.append("More consistent reaction times")
        
        # Check for reduced anxiety indicators
        first_anxiety = np.mean([s['anxiety_score'] for s in first_half])
        second_anxiety = np.mean([s['anxiety_score'] for s in second_half])
        
        if second_anxiety < first_anxiety - 15:
            improvements.append("Reduced anxiety indicators")
        
        return improvements
    
    def _default_analysis(self):
        """Default analysis for users with no data"""
        return {
            'anxiety_trend': 'stable',
            'depression_trend': 'stable',
            'attention_trend': 'stable',
            'most_recent_scores': {'anxiety': 0, 'depression': 0, 'attention': 50},
            'average_scores': {'anxiety': 0, 'depression': 0, 'attention': 50},
            'session_count': 0,
            'improvement_indicators': []
        }
