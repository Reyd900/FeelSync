"""
ML Pipeline Utilities for FeelSync
Provides utilities for data preprocessing, feature engineering, and model evaluation.
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
import joblib
import logging
from typing import Tuple, Dict, Any, List
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FeaturePipeline:
    """Feature engineering pipeline for emotion detection."""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.fitted = False
    
    def extract_text_features(self, texts: List[str]) -> pd.DataFrame:
        """Extract features from text data."""
        features = []
        
        for text in texts:
            text_lower = text.lower()
            feature_dict = {
                'text_length': len(text),
                'word_count': len(text.split()),
                'avg_word_length': np.mean([len(word) for word in text.split()]) if text.split() else 0,
                'exclamation_count': text.count('!'),
                'question_count': text.count('?'),
                'uppercase_ratio': sum(1 for c in text if c.isupper()) / len(text) if text else 0,
                'contains_positive_words': any(word in text_lower for word in ['happy', 'joy', 'love', 'great', 'good', 'amazing']),
                'contains_negative_words': any(word in text_lower for word in ['sad', 'angry', 'hate', 'bad', 'terrible', 'awful']),
                'contains_neutral_words': any(word in text_lower for word in ['okay', 'fine', 'normal', 'maybe', 'perhaps'])
            }
            features.append(feature_dict)
        
        return pd.DataFrame(features)
    
    def extract_audio_features(self, audio_data: List[Dict]) -> pd.DataFrame:
        """Extract features from audio data (mock implementation)."""
        features = []
        
        for audio in audio_data:
            feature_dict = {
                'pitch_mean': np.random.normal(150, 30),  # Mock pitch
                'pitch_std': np.random.normal(20, 5),
                'energy_mean': np.random.normal(0.5, 0.1),
                'energy_std': np.random.normal(0.1, 0.02),
                'tempo': np.random.normal(120, 20),
                'spectral_centroid': np.random.normal(2000, 500),
                'zero_crossing_rate': np.random.normal(0.1, 0.02),
                'mfcc_1': np.random.normal(0, 1),
                'mfcc_2': np.random.normal(0, 1),
                'mfcc_3': np.random.normal(0, 1)
            }
            features.append(feature_dict)
        
        return pd.DataFrame(features)
    
    def fit_transform(self, X: pd.DataFrame, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Fit the pipeline and transform the data."""
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Encode labels
        y_encoded = self.label_encoder.fit_transform(y)
        
        self.fitted = True
        logger.info(f"Pipeline fitted. Feature shape: {X_scaled.shape}, Classes: {self.label_encoder.classes_}")
        
        return X_scaled, y_encoded
    
    def transform(self, X: pd.DataFrame) -> np.ndarray:
        """Transform new data using fitted pipeline."""
        if not self.fitted:
            raise ValueError("Pipeline not fitted. Call fit_transform first.")
        
        return self.scaler.transform(X)
    
    def inverse_transform_labels(self, y_encoded: np.ndarray) -> np.ndarray:
        """Convert encoded labels back to original labels."""
        return self.label_encoder.inverse_transform(y_encoded)
    
    def save(self, path: str):
        """Save the fitted pipeline."""
        pipeline_data = {
            'scaler': self.scaler,
            'label_encoder': self.label_encoder,
            'fitted': self.fitted
        }
        joblib.dump(pipeline_data, path)
        logger.info(f"Pipeline saved to {path}")
    
    def load(self, path: str):
        """Load a fitted pipeline."""
        pipeline_data = joblib.load(path)
        self.scaler = pipeline_data['scaler']
        self.label_encoder = pipeline_data['label_encoder']
        self.fitted = pipeline_data['fitted']
        logger.info(f"Pipeline loaded from {path}")

class ModelTrainer:
    """Train and evaluate multiple models for emotion detection."""
    
    def __init__(self):
        self.models = {
            'random_forest': RandomForestClassifier(n_estimators=100, random_state=42),
            'svm': SVC(kernel='rbf', random_state=42),
            'logistic_regression': LogisticRegression(random_state=42, max_iter=1000)
        }
        self.trained_models = {}
        self.best_model = None
        self.best_score = 0
    
    def train_models(self, X: np.ndarray, y: np.ndarray) -> Dict[str, Dict[str, Any]]:
        """Train all models and return performance metrics."""
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
        
        results = {}
        
        for name, model in self.models.items():
            logger.info(f"Training {name}...")
            
            # Train model
            model.fit(X_train, y_train)
            
            # Make predictions
            y_pred = model.predict(X_test)
            
            # Calculate metrics
            accuracy = accuracy_score(y_test, y_pred)
            cv_scores = cross_val_score(model, X_train, y_train, cv=5)
            
            results[name] = {
                'model': model,
                'accuracy': accuracy,
                'cv_mean': cv_scores.mean(),
                'cv_std': cv_scores.std(),
                'classification_report': classification_report(y_test, y_pred),
                'confusion_matrix': confusion_matrix(y_test, y_pred)
            }
            
            # Track best model
            if accuracy > self.best_score:
                self.best_score = accuracy
                self.best_model = name
            
            logger.info(f"{name} - Accuracy: {accuracy:.4f}, CV: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
        
        self.trained_models = results
        logger.info(f"Best model: {self.best_model} with accuracy: {self.best_score:.4f}")
        
        return results
    
    def get_best_model(self):
        """Get the best performing model."""
        if not self.trained_models:
            raise ValueError("No models trained yet.")
        
        return self.trained_models[self.best_model]['model']
    
    def save_model(self, model_name: str, path: str):
        """Save a specific model."""
        if model_name not in self.trained_models:
            raise ValueError(f"Model {model_name} not found.")
        
        model = self.trained_models[model_name]['model']
        joblib.dump(model, path)
        logger.info(f"Model {model_name} saved to {path}")
    
    def load_model(self, path: str):
        """Load a model from disk."""
        return joblib.load(path)

class DataValidator:
    """Validate and clean data for ML pipeline."""
    
    @staticmethod
    def validate_features(X: pd.DataFrame) -> Tuple[bool, List[str]]:
        """Validate feature data."""
        issues = []
        
        # Check for missing values
        if X.isnull().any().any():
            issues.append("Missing values found in features")
        
        # Check for infinite values
        if np.isinf(X.select_dtypes(include=[np.number])).any().any():
            issues.append("Infinite values found in features")
        
        # Check for constant features
        constant_features = X.columns[X.nunique() <= 1].tolist()
        if constant_features:
            issues.append(f"Constant features found: {constant_features}")
        
        return len(issues) == 0, issues
    
    @staticmethod
    def clean_data(X: pd.DataFrame, y: np.ndarray = None) -> Tuple[pd.DataFrame, np.ndarray]:
        """Clean the data by handling missing values and outliers."""
        logger.info("Cleaning data...")
        
        # Handle missing values
        X_clean = X.fillna(X.mean())
        
        # Remove constant features
        constant_features = X_clean.columns[X_clean.nunique() <= 1].tolist()
        if constant_features:
            X_clean = X_clean.drop(columns=constant_features)
            logger.info(f"Removed constant features: {constant_features}")
        
        # Handle outliers using IQR method
        numeric_columns = X_clean.select_dtypes(include=[np.number]).columns
        for col in numeric_columns:
            Q1 = X_clean[col].quantile(0.25)
            Q3 = X_clean[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            X_clean[col] = X_clean[col].clip(lower_bound, upper_bound)
        
        logger.info(f"Data cleaned. Shape: {X_clean.shape}")
        
        return X_clean, y

def create_ensemble_model(models: List[Any], weights: List[float] = None) -> 'EnsembleModel':
    """Create an ensemble model from multiple trained models."""
    return EnsembleModel(models, weights)

class EnsembleModel:
    """Ensemble model that combines predictions from multiple models."""
    
    def __init__(self, models: List[Any], weights: List[float] = None):
        self.models = models
        self.weights = weights or [1.0] * len(models)
        self.weights = np.array(self.weights) / sum(self.weights)  # Normalize weights
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions using weighted ensemble."""
        predictions = []
        
        for model in self.models:
            pred = model.predict_proba(X) if hasattr(model, 'predict_proba') else model.predict(X)
            predictions.append(pred)
        
        # Weighted average
        ensemble_pred = np.average(predictions, axis=0, weights=self.weights)
        
        # Convert to class predictions if needed
        if len(ensemble_pred.shape) > 1:
            return np.argmax(ensemble_pred, axis=1)
        else:
            return ensemble_pred
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Make probability predictions using weighted ensemble."""
        predictions = []
        
        for model in self.models:
            if hasattr(model, 'predict_proba'):
                pred = model.predict_proba(X)
            else:
                # Convert binary predictions to probabilities
                pred = model.predict(X)
                pred = np.column_stack([1 - pred, pred])
            predictions.append(pred)
        
        return np.average(predictions, axis=0, weights=self.weights)

def evaluate_model_performance(model: Any, X_test: np.ndarray, y_test: np.ndarray, 
                             label_encoder: LabelEncoder = None) -> Dict[str, Any]:
    """Comprehensive model evaluation."""
    y_pred = model.predict(X_test)
    
    # Convert back to original labels if encoder provided
    if label_encoder:
        y_test_labels = label_encoder.inverse_transform(y_test)
        y_pred_labels = label_encoder.inverse_transform(y_pred)
    else:
        y_test_labels = y_test
        y_pred_labels = y_pred
    
    metrics = {
        'accuracy': accuracy_score(y_test, y_pred),
        'classification_report': classification_report(y_test_labels, y_pred_labels),
        'confusion_matrix': confusion_matrix(y_test, y_pred),
        'class_distribution': np.bincount(y_test) / len(y_test)
    }
    
    return metrics

def save_pipeline_artifacts(pipeline: FeaturePipeline, model: Any, 
                          metrics: Dict[str, Any], save_dir: str):
    """Save all pipeline artifacts."""
    os.makedirs(save_dir, exist_ok=True)
    
    # Save pipeline
    pipeline.save(os.path.join(save_dir, 'pipeline.pkl'))
    
    # Save model
    joblib.dump(model, os.path.join(save_dir, 'model.pkl'))
    
    # Save metrics
    joblib.dump(metrics, os.path.join(save_dir, 'metrics.pkl'))
    
    logger.info(f"All artifacts saved to {save_dir}")

if __name__ == "__main__":
    # Example usage
    logger.info("ML Pipeline utilities loaded successfully!")
    
    # Create sample data for testing
    sample_texts = [
        "I'm feeling great today!",
        "This is terrible news",
        "It's an okay day, nothing special",
        "I love this amazing weather!",
        "I'm so angry about this situation"
    ]
    
    sample_labels = ['happy', 'sad', 'neutral', 'happy', 'angry']
    
    # Initialize pipeline
    pipeline = FeaturePipeline()
    
    # Extract features
    features = pipeline.extract_text_features(sample_texts)
    print("Sample features:")
    print(features.head())
    
    # Fit pipeline
    X_scaled, y_encoded = pipeline.fit_transform(features, np.array(sample_labels))
    print(f"\nScaled features shape: {X_scaled.shape}")
    print(f"Label classes: {pipeline.label_encoder.classes_}")
