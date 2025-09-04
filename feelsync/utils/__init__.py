"""
FeelSync Utilities Package

This package contains utility functions for data preprocessing,
machine learning pipeline management, and various helper functions.
"""

from .data_preprocessing import (
    DataPreprocessor,
    MoodDataCleaner,
    FeatureEngineer,
    DataValidator
)

from .ml_pipeline import (
    MLPipeline,
    ModelTrainer,
    ModelEvaluator,
    PredictionEngine
)

__version__ = "1.0.0"
__all__ = [
    "DataPreprocessor",
    "MoodDataCleaner", 
    "FeatureEngineer",
    "DataValidator",
    "MLPipeline",
    "ModelTrainer",
    "ModelEvaluator",
    "PredictionEngine"
]

# Global configuration
UTILS_CONFIG = {
    "data_preprocessing": {
        "missing_value_strategy": "interpolate",
        "outlier_detection_method": "iqr",
        "normalization_method": "standard",
        "feature_selection_threshold": 0.05
    },
    "ml_pipeline": {
        "train_test_split": 0.8,
        "cross_validation_folds": 5,
        "random_state": 42,
        "model_selection_metric": "r2_score"
    },
    "logging": {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    }
}

def get_config(section=None):
    """Get configuration settings."""
    if section:
        return UTILS_CONFIG.get(section, {})
    return UTILS_CONFIG
