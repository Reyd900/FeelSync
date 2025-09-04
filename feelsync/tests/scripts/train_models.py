#!/usr/bin/env python3
"""
Model Training Script for FeelSync
Trains emotion detection models using text and audio data.
"""

import os
import sys
import argparse
import pandas as pd
import numpy as np
import logging
from datetime import datetime
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.ml_pipeline import FeaturePipeline, ModelTrainer, DataValidator, save_pipeline_artifacts, evaluate_model_performance
from database.db_manager import DatabaseManager
from config.settings import ML_CONFIG, DATABASE_CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_training_data(db_manager: DatabaseManager, limit: int = None) -> tuple:
    """Load training data from database."""
    logger.info("Loading training data from database...")
    
    # Get emotion entries with text
    query = """
    SELECT 
        e.id,
        e.user_id,
        e.emotion,
        e.intensity,
        e.description,
        e.timestamp,
        a.file_path as audio_path,
        a.duration as audio_duration
    FROM emotions e
    LEFT JOIN audio_logs a ON e.id = a.emotion_id
    WHERE e.description IS NOT NULL AND e.description != ''
    ORDER BY e.timestamp DESC
    """
    
    if limit:
        query += f" LIMIT {limit}"
    
    data = db_manager.fetch_all(query)
    
    if not data:
        raise ValueError("No training data found in database")
    
    df = pd.DataFrame(data, columns=['id', 'user_id', 'emotion', 'intensity', 'description', 'timestamp', 'audio_path', 'audio_duration'])
    
    logger.info(f"Loaded {len(df)} samples")
    logger.info(f"Emotion distribution:\n{df['emotion'].value_counts()}")
    
    return df

def prepare_features(df: pd.DataFrame, pipeline: FeaturePipeline) -> tuple:
    """Prepare features from the data."""
    logger.info("Preparing features...")
    
    # Extract text features
    text_features = pipeline.extract_text_features(df['description'].tolist())
    
    # Add intensity as a feature
    text_features['intensity'] = df['intensity'].values
    
    # Add audio features for samples with audio
    has_audio = df['audio_path'].notna()
    audio_data = []
    
    for idx, row in df.iterrows():
        if pd.notna(row['audio_path']) and os.path.exists(row['audio_path']):
            # Mock audio data - in real implementation, extract actual audio features
            audio_data.append({'file_path': row['audio_path'], 'duration': row['audio_duration']})
        else:
            audio_data.append({'file_path': None, 'duration': 0})
    
    if audio_data:
        audio_features = pipeline.extract_audio_features(audio_data)
        # Combine text and audio features
        features = pd.concat([text_features, audio_features], axis=1)
    else:
        features = text_features
    
    # Add temporal features
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    features['hour_of_day'] = df['timestamp'].dt.hour
    features['day_of_week'] = df['timestamp'].dt.dayofweek
    features['is_weekend'] = (df['timestamp'].dt.dayofweek >= 5).astype(int)
    
    logger.info(f"Feature matrix shape: {features.shape}")
    logger.info(f"Features: {list(features.columns)}")
    
    return features, df['emotion'].values

def train_and_evaluate_models(X: np.ndarray, y: np.ndarray, pipeline: FeaturePipeline) -> dict:
    """Train multiple models and return the best one."""
    logger.info("Training models...")
    
    trainer = ModelTrainer()
    results = trainer.train_models(X, y)
    
    # Print results
    logger.info("\n" + "="*50)
    logger.info("MODEL TRAINING RESULTS")
    logger.info("="*50)
    
    for name, result in results.items():
        logger.info(f"\n{name.upper()}:")
        logger.info(f"Accuracy: {result['accuracy']:.4f}")
        logger.info(f"Cross-validation: {result['cv_mean']:.4f} (+/- {result['cv_std'] * 2:.4f})")
        logger.info(f"Classification Report:\n{result['classification_report']}")
    
    logger.info(f"\nBest model: {trainer.best_model} with accuracy: {trainer.best_score:.4f}")
    
    # Get best model
    best_model = trainer.get_best_model()
    
    return {
        'best_model': best_model,
        'best_model_name': trainer.best_model,
        'all_results': results,
        'trainer': trainer
    }

def save_model_artifacts(pipeline: FeaturePipeline, model_data: dict, save_dir: str):
    """Save all model artifacts."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_dir = os.path.join(save_dir, f"model_{timestamp}")
    os.makedirs(model_dir, exist_ok=True)
    
    # Save pipeline and best model
    save_pipeline_artifacts(
        pipeline=pipeline,
        model=model_data['best_model'],
        metrics=model_data['all_results'],
        save_dir=model_dir
    )
    
    # Save training metadata
    metadata = {
        'timestamp': timestamp,
        'best_model': model_data['best_model_name'],
        'training_config': ML_CONFIG,
        'feature_count': len(pipeline.scaler.feature_names_in_) if hasattr(pipeline.scaler, 'feature_names_in_') else 'unknown'
    }
    
    with open(os.path.join(model_dir, 'metadata.json'), 'w') as f:
        json.dump(metadata, f, indent=2, default=str)
    
    # Create symlink to latest model
    latest_link = os.path.join(save_dir, 'latest')
    if os.path.islink(latest_link):
        os.unlink(latest_link)
    os.symlink(model_dir, latest_link)
    
    logger.info(f"Model artifacts saved to: {model_dir}")
    return model_dir

def validate_data_quality(df: pd.DataFrame):
    """Validate data quality and log issues."""
    logger.info("Validating data quality...")
    
    issues = []
    
    # Check for missing values
    missing_text = df['description'].isna().sum()
    if missing_text > 0:
        issues.append(f"{missing_text} samples missing text descriptions")
    
    # Check emotion distribution
    emotion_counts = df['emotion'].value_counts()
    min_samples = emotion_counts.min()
    if min_samples < 10:
        issues.append(f"Some emotions have very few samples (min: {min_samples})")
    
    # Check for duplicate descriptions
    duplicates = df['description'].duplicated().sum()
    if duplicates > 0:
        issues.append(f"{duplicates} duplicate descriptions found")
    
    # Check text length distribution
    text_lengths = df['description'].str.len()
    very_short = (text_lengths < 5).sum()
    if very_short > 0:
        issues.append(f"{very_short} very short descriptions (< 5 characters)")
    
    if issues:
        logger.warning("Data quality issues found:")
        for issue in issues:
            logger.warning(f"  - {issue}")
    else:
        logger.info("Data quality checks passed!")
    
    return issues

def main():
    parser = argparse.ArgumentParser(description="Train FeelSync emotion detection models")
    parser.add_argument('--data-limit', type=int, help='Limit number of training samples')
    parser.add_argument('--output-dir', type=str, default='models/', help='Directory to save models')
    parser.add_argument('--validate-only', action='store_true', help='Only validate data, don\'t train')
    parser.add_argument('--config-file', type=str, help='Path to custom config file')
    
    args = parser.parse_args()
    
    logger.info("Starting FeelSync model training...")
    logger.info(f"Arguments: {vars(args)}")
    
    try:
        # Initialize database connection
        db_manager = DatabaseManager()
        db_manager.connect()
        
        # Load training data
        df = load_training_data(db_manager, limit=args.data_limit)
        
        # Validate data quality
        data_issues = validate_data_quality(df)
        
        if args.validate_only:
            logger.info("Data validation complete. Exiting.")
            return
        
        # Initialize feature pipeline
        pipeline = FeaturePipeline()
        
        # Prepare features
        X, y = prepare_features(df, pipeline)
        
        # Validate features
        is_valid, feature_issues = DataValidator.validate_features(X)
        if not is_valid:
            logger.warning("Feature validation issues:")
            for issue in feature_issues:
                logger.warning(f"  - {issue}")
            
            # Clean data
            X, y = DataValidator.clean_data(X, y)
        
        # Fit pipeline and transform data
        X_scaled, y_encoded = pipeline.fit_transform(X, y)
        
        # Train models
        model_data = train_and_evaluate_models(X_scaled, y_encoded, pipeline)
        
        # Save artifacts
        model_dir = save_model_artifacts(pipeline, model_data, args.output_dir)
        
        # Final evaluation
        logger.info("\n" + "="*50)
        logger.info("TRAINING COMPLETE")
        logger.info("="*50)
        logger.info(f"Best model: {model_data['best_model_name']}")
        logger.info(f"Training samples: {len(df)}")
        logger.info(f"Features: {X_scaled.shape[1]}")
        logger.info(f"Classes: {len(pipeline.label_encoder.classes_)}")
        logger.info(f"Model saved to: {model_dir}")
        
        # Generate training report
        report_path = os.path.join(model_dir, 'training_report.txt')
        with open(report_path, 'w') as f:
            f.write("FeelSync Model Training Report\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Training Date: {datetime.now()}\n")
            f.write(f"Training Samples: {len(df)}\n")
            f.write(f"Features: {X_scaled.shape[1]}\n")
            f.write(f"Classes: {list(pipeline.label_encoder.classes_)}\n")
            f.write(f"Best Model: {model_data['best_model_name']}\n")
            f.write(f"Best Accuracy: {model_data['trainer'].best_score:.4f}\n\n")
            
            f.write("Emotion Distribution:\n")
            f.write(df['emotion'].value_counts().to_string())
            f.write("\n\n")
            
            if data_issues:
                f.write("Data Quality Issues:\n")
                for issue in data_issues:
                    f.write(f"- {issue}\n")
                f.write("\n")
            
            f.write("Model Performance:\n")
            for name, result in model_data['all_results'].items():
                f.write(f"\n{name}:\n")
                f.write(f"Accuracy: {result['accuracy']:.4f}\n")
                f.write(f"CV Score: {result['cv_mean']:.4f} (+/- {result['cv_std'] * 2:.4f})\n")
        
        logger.info(f"Training report saved to: {report_path}")
        
    except Exception as e:
        logger.error(f"Training failed: {str(e)}")
        raise
    
    finally:
        if 'db_manager' in locals():
            db_manager.disconnect()

if __name__ == "__main__":
    main()
