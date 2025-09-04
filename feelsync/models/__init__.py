"""
FeelSync Models Package

This package contains machine learning models for mood prediction,
behavioral pattern analysis, and therapeutic insights.
"""

from .mood_predictor import MoodPredictor
from .behavioral_analyzer import BehavioralAnalyzer
from .therapy_insights import TherapyInsights

__version__ = "1.0.0"
__all__ = ["MoodPredictor", "BehavioralAnalyzer", "TherapyInsights"]

# Model configurations
MODEL_CONFIG = {
    "mood_predictor": {
        "algorithm": "random_forest",
        "features": ["sleep_hours", "stress_level", "social_interaction", "exercise_minutes"],
        "target": "mood_score",
        "model_path": "models/mood_predictor.joblib"
    },
    "behavioral_analyzer": {
        "algorithm": "clustering",
        "features": ["activity_frequency", "mood_variance", "check_in_consistency"],
        "model_path": "models/behavioral_analyzer.joblib"
    },
    "therapy_insights": {
        "algorithm": "pattern_matching",
        "features": ["mood_trends", "factor_correlations", "intervention_responses"],
        "model_path": "models/therapy_insights.joblib"
    }
}

def get_model_config(model_name):
    """Get configuration for a specific model."""
    return MODEL_CONFIG.get(model_name, {})

def list_available_models():
    """List all available models."""
    return list(MODEL_CONFIG.keys())
