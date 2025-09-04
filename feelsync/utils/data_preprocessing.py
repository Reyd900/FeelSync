"""
Data Preprocessing Utilities for FeelSync

This module contains classes and functions for cleaning, preprocessing,
and feature engineering of mood tracking data.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Union
import json
import logging
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.impute import SimpleImputer, KNNImputer
from scipy import stats
import warnings

warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataValidator:
    """Validate and check data quality for mood tracking data."""
    
    def __init__(self):
        self.validation_rules = {
            'mood_score': {'min': 1.0, 'max': 5.0, 'type': float},
            'sleep_hours': {'min': 0.0, 'max': 24.0, 'type': float},
            'stress_level': {'min': 1, 'max': 10, 'type': int},
            'exercise_minutes': {'min': 0, 'max': 480, 'type': int},
            'social_interaction': {'min': 0, 'max': 10, 'type': int},
            'work_hours': {'min': 0, 'max': 24, 'type': float},
            'intensity': {'min': 1, 'max': 10, 'type': int}
        }
    
    def validate_dataframe(self, df: pd.DataFrame) -> Dict[str, any]:
        """Validate entire dataframe and return validation report."""
        report = {
            'total_rows': len(df),
            'issues': [],
            'warnings': [],
            'data_quality_score': 0.0,
            'valid_rows': 0
        }
        
        # Check required columns
        required_cols = ['user_id', 'date', 'mood_score']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            report['issues'].append(f"Missing required columns: {missing_cols}")
            return report
        
        # Validate each row
        valid_rows = 0
        for idx, row in df.iterrows():
            row_valid = True
            
            # Check data types and ranges
            for col, rules in self.validation_rules.items():
                if col in df.columns:
                    value = row[col]
                    if pd.isna(value):
                        continue
                    
                    # Type validation
                    try:
                        if rules['type'] == int:
                            value = int(float(value))
                        elif rules['type'] == float:
                            value = float(value)
                    except (ValueError, TypeError):
                        report['issues'].append(f"Row {idx}: Invalid type for {col}: {value}")
                        row_valid = False
                        continue
                    
                    # Range validation
                    if value < rules['min'] or value > rules['max']:
                        report['warnings'].append(f"Row {idx}: {col} value {value} outside expected range [{rules['min']}, {rules['max']}]")
            
            # Date validation
            try:
                pd.to_datetime(row['date'])
            except:
                report['issues'].append(f"Row {idx}: Invalid date format: {row['date']}")
                row_valid = False
            
            if row_valid:
                valid_rows += 1
        
        report['valid_rows'] = valid_rows
        report['data_quality_score'] = valid_rows / len(df) if len(df) > 0 else 0.0
        
        return report
    
    def clean_invalid_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove or fix invalid data points."""
        df_cleaned = df.copy()
        
        # Remove rows with invalid mood scores
        df_cleaned = df_cleaned[
            (df_cleaned['mood_score'] >= 1.0) & 
            (df_cleaned['mood_score'] <= 5.0)
        ]
        
        # Cap values at reasonable limits
        for col, rules in self.validation_rules.items():
            if col in df_cleaned.columns:
                df_cleaned[col] = df_cleaned[col].clip(
                    lower=rules['min'], 
                    upper=rules['max']
                )
        
        # Remove rows with invalid dates
        df_cleaned['date'] = pd.to_datetime(df_cleaned['date'], errors='coerce')
        df_cleaned = df_cleaned.dropna(subset=['date'])
        
        logger.info(f"Data cleaning: {len(df)} -> {len(df_cleaned)} rows")
        return df_cleaned


class MoodDataCleaner:
    """Clean and preprocess mood tracking data."""
    
    def __init__(self):
        self.validator = DataValidator()
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Main data cleaning pipeline."""
        logger.info("Starting data cleaning process...")
        
        # Validate and clean
        df_clean = self.validator.clean_invalid_data(df)
        
        # Handle duplicates
        df_clean = self._remove_duplicates(df_clean)
        
        # Sort by user and date
        df_clean = df_clean.sort_values(['user_id', 'date'])
        
        # Handle missing values
        df_clean = self._handle_missing_values(df_clean)
        
        # Parse mood factors
        df_clean = self._parse_mood_factors(df_clean)
        
        logger.info("Data cleaning completed successfully")
        return df_clean
    
    def _remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove duplicate entries for same user on same date."""
        before_count = len(df)
        
        # Keep the latest entry for each user-date combination
        df_dedup = df.sort_values('date').drop_duplicates(
            subset=['user_id', 'date'], 
            keep='last'
        )
        
        removed_count = before_count - len(df_dedup)
        if removed_count > 0:
            logger.info(f"Removed {removed_count} duplicate entries")
        
        return df_dedup
    
    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values using appropriate strategies."""
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_columns:
            if col == 'mood_score':
                # Don't impute mood scores - these are critical
                continue
            
            # Use forward fill for time series data, then backward fill
            df[col] = df.groupby('user_id')[col].fillna(method='ffill')
            df[col] = df.groupby('user_id')[col].fillna(method='bfill')
            
            # If still missing, use median
            if df[col].isna().any():
                median_val = df[col].median()
                df[col] = df[col].fillna(median_val)
        
        return df
    
    def _parse_mood_factors(self, df: pd.DataFrame) -> pd.DataFrame:
        """Parse and encode mood factors."""
        if 'mood_factors' in df.columns:
            # Create binary columns for each mood factor
            all_factors = set()
            
            # Collect all unique factors
            for factors_str in df['mood_factors'].dropna():
                if isinstance(factors_str, str):
                    factors = [f.strip() for f in factors_str.split(',')]
                    all_factors.update(factors)
            
            # Create binary columns
            for factor in all_factors:
                col_name = f"factor_{factor.lower().replace(' ', '_')}"
                df[col_name] = df['mood_factors'].apply(
                    lambda x: 1 if isinstance(x, str) and factor in x else 0
                )
        
        return df


class FeatureEngineer:
    """Create and engineer features for machine learning."""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.label_encoders = {}
    
    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create engineered features from raw data."""
        logger.info("Starting feature engineering...")
        
        df_features = df.copy()
        
        # Time-based features
        df_features = self._create_time_features(df_features)
        
        # Trend features
        df_features = self._create_trend_features(df_features)
        
        # Interaction features
        df_features = self._create_interaction_features(df_features)
        
        # Statistical features
        df_features = self._create_statistical_features(df_features)
        
        # Behavioral pattern features
        df_features = self._create_pattern_features(df_features)
        
        logger.info("Feature engineering completed")
        return df_features
    
    def _create_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create time-based features."""
        df['date'] = pd.to_datetime(df['date'])
        
        # Basic time features
        df['day_of_week'] = df['date'].dt.dayofweek
        df['month'] = df['date'].dt.month
        df['quarter'] = df['date'].dt.quarter
        df['is_weekend'] = (df['day_of_week'].isin([5, 6])).astype(int)
        df['is_monday'] = (df['day_of_week'] == 0).astype(int)
        
        # Cyclical encoding for day of week
        df['day_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['day_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
        
        # Cyclical encoding for month
        df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
        df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
        
        return df
    
    def _create_trend_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create trend and moving average features."""
        for user in df['user_id'].unique():
            user_mask = df['user_id'] == user
            user_data = df[user_mask].sort_values('date')
            
            # Moving averages (3, 7, 14 days)
            for window in [3, 7, 14]:
                col_name = f'mood_ma_{window}d'
                df.loc[user_mask, col_name] = user_data['mood_score'].rolling(
                    window=window, min_periods=1
                ).mean()
                
                # Mood volatility (rolling standard deviation)
                vol_col = f'mood_volatility_{window}d'
                df.loc[user_mask, vol_col] = user_data['mood_score'].rolling(
                    window=window, min_periods=1
                ).std()
            
            # Mood trend (difference from moving average)
            df.loc[user_mask, 'mood_trend_7d'] = (
                df.loc[user_mask, 'mood_score'] - 
                df.loc[user_mask, 'mood_ma_7d']
            )
            
            # Days since last high/low mood
            high_mood_dates = user_data[user_data['mood_score'] >= 4.5]['date']
            low_mood_dates = user_data[user_data['mood_score'] <= 2.5]['date']
            
            for idx, row in user_data.iterrows():
                current_date = row['date']
                
                # Days since last high mood
                recent_high_dates = high_mood_dates[high_mood_dates <= current_date]
                if len(recent_high_dates) > 0:
                    days_since_high = (current_date - recent_high_dates.max()).days
                else:
                    days_since_high = 999  # No previous high mood
                df.loc[idx, 'days_since_high_mood'] = days_since_high
                
                # Days since last low mood
                recent_low_dates = low_mood_dates[low_mood_dates <= current_date]
                if len(recent_low_dates) > 0:
                    days_since_low = (current_date - recent_low_dates.max()).days
                else:
                    days_since_low = 999  # No previous low mood
                df.loc[idx, 'days_since_low_mood'] = days_since_low
        
        return df
    
    def _create_interaction_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create interaction features between variables."""
        # Sleep-stress interaction
        df['sleep_stress_interaction'] = df['sleep_hours'] * (10 - df['stress_level'])
        
        # Exercise-social interaction
        if 'exercise_minutes' in df.columns and 'social_interaction' in df.columns:
            df['exercise_social_balance'] = (
                df['exercise_minutes'] / 60 + df['social_interaction']
            )
        
        # Work-life balance score
        if 'work_hours' in df.columns and 'family_time' in df.columns:
            df['work_life_balance'] = df['family_time'] / (df['work_hours'] + 1)
        
        # Health-wellness composite
        health_components = []
        if 'sleep_hours' in df.columns:
            health_components.append('sleep_hours')
        if 'exercise_minutes' in df.columns:
            health_components.append('exercise_minutes')
        
        if health_components:
            df['wellness_composite'] = df[health_components].apply(
                lambda x: np.mean([(x['sleep_hours'] / 8), 
                                 (x.get('exercise_minutes', 0) / 60)]), 
                axis=1
            )
        
        return df
    
    def _create_statistical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create statistical features for each user."""
        for user in df['user_id'].unique():
            user_mask = df['user_id'] == user
            user_data = df[user_mask]
            
            # User-specific statistics
            user_mood_mean = user_data['mood_score'].mean()
            user_mood_std = user_data['mood_score'].std()
            
            df.loc[user_mask, 'user_mood_mean'] = user_mood_mean
            df.loc[user_mask, 'user_mood_std'] = user_mood_std
            
            # Z-score of current mood relative to user's history
            df.loc[user_mask, 'mood_zscore'] = (
                (df.loc[user_mask, 'mood_score'] - user_mood_mean) / 
                (user_mood_std + 1e-8)  # Add small epsilon to avoid division by zero
            )
            
            # Percentile rank of current mood
            df.loc[user_mask, 'mood_percentile'] = df.loc[user_mask, 'mood_score'].rank(pct=True)
        
        return df
    
    def _create_pattern_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create features based on behavioral patterns."""
        for user in df['user_id'].unique():
            user_mask = df['user_id'] == user
            user_data = df[user_mask].sort_values('date')
            
            # Streak calculations
            mood_threshold = 3.5
            df.loc[user_mask, 'positive_mood_streak'] = self._calculate_streak(
                user_data['mood_score'] >= mood_threshold
            )
            df.loc[user_mask, 'negative_mood_streak'] = self._calculate_streak(
                user_data['mood_score'] < mood_threshold
            )
            
            # Consistency measures
            if len(user_data) > 7:
                # Mood consistency (inverse of coefficient of variation)
                recent_data = user_data.tail(7)
                mood_cv = recent_data['mood_score'].std() / (recent_data['mood_score'].mean() + 1e-8)
                df.loc[user_mask, 'mood_consistency_7d'] = 1 / (1 + mood_cv)
        
        return df
    
    def _calculate_streak(self, boolean_series: pd.Series) -> pd.Series:
        """Calculate current streak of True values."""
        # Create groups of consecutive True/False values
        groups = boolean_series.ne(boolean_series.shift()).cumsum()
        
        # For each group of True values, calculate the streak length
        streaks = boolean_series.groupby(groups).cumsum()
        
        # Set streaks to 0 where the original series was False
        streaks = streaks.where(boolean_series, 0)
        
        return streaks
    
    def scale_features(self, df: pd.DataFrame, fit: bool = True) -> pd.DataFrame:
        """Scale numerical features."""
        numerical_columns = df.select_dtypes(include=[np.number]).columns
        
        # Exclude certain columns from scaling
        exclude_columns = ['user_id', 'mood_score', 'day_of_week', 'month', 
                          'is_weekend', 'is_monday']
        scale_columns = [col for col in numerical_columns if col not in exclude_columns]
        
        if fit:
            df[scale_columns] = self.scaler.fit_transform(df[scale_columns])
        else:
            df[scale_columns] = self.scaler.transform(df[scale_columns])
        
        return df


class DataPreprocessor:
    """Main data preprocessing pipeline."""
    
    def __init__(self):
        self.cleaner = MoodDataCleaner()
        self.engineer = FeatureEngineer()
        self.validator = DataValidator()
    
    def preprocess(self, df: pd.DataFrame, fit_scalers: bool = True) -> Tuple[pd.DataFrame, Dict]:
        """Complete preprocessing pipeline."""
        logger.info("Starting complete data preprocessing...")
        
        # Step 1: Validate raw data
        validation_report = self.validator.validate_dataframe(df)
        
        # Step 2: Clean data
        df_clean = self.cleaner.clean_data(df)
        
        # Step 3: Feature engineering
        df_features = self.engineer.create_features(df_clean)
        
        # Step 4: Scale features
        df_scaled = self.engineer.scale_features(df_features, fit=fit_scalers)
        
        # Prepare final report
        preprocessing_report = {
            'original_rows': len(df),
            'final_rows': len(df_scaled),
            'data_quality_score': validation_report['data_quality_score'],
            'features_created': len(df_scaled.columns) - len(df.columns),
            'validation_issues': validation_report.get('issues', []),
            'validation_warnings': validation_report.get('warnings', [])
        }
        
        logger.info(f"Preprocessing completed: {len(df)} -> {len(df_scaled)} rows, {len(df_scaled.columns)} features")
        
        return df_scaled, preprocessing_report
    
    def prepare_for_ml(self, df: pd.DataFrame, target_column: str = 'mood_score') -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare data specifically for machine learning."""
        # Remove non-feature columns
        feature_columns = df.columns.drop([
            'user_id', 'date', target_column, 'notes', 'mood_factors'
        ] + [col for col in df.columns if col.startswith('factor_')])
        
        X = df[feature_columns]
        y = df[target_column] if target_column in df.columns else None
        
        # Handle any remaining categorical variables
        categorical_columns = X.select_dtypes(include=['object']).columns
        for col in categorical_columns:
            if col not in self.engineer.label_encoders:
                self.engineer.label_encoders[col] = LabelEncoder()
                X[col] = self.engineer.label_encoders[col].fit_transform(X[col].astype(str))
            else:
                X[col] = self.engineer.label_encoders[col].transform(X[col].astype(str))
        
        return X, y
    
    def detect_outliers(self, df: pd.DataFrame, method: str = 'iqr') -> Dict[str, List]:
        """Detect outliers in the data."""
        outliers = {}
        numerical_columns = df.select_dtypes(include=[np.number]).columns
        
        for col in numerical_columns:
            if method == 'iqr':
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                outlier_mask = (df[col] < lower_bound) | (df[col] > upper_bound)
                outliers[col] = df.index[outlier_mask].tolist()
            
            elif method == 'zscore':
                z_scores = np.abs(stats.zscore(df[col].dropna()))
                outlier_mask = z_scores > 3
                outliers[col] = df.index[outlier_mask].tolist()
        
        return outliers
    
    def create_user_profiles(self, df: pd.DataFrame) -> Dict[str, Dict]:
        """Create comprehensive user profiles for personalization."""
        user_profiles = {}
        
        for user_id in df['user_id'].unique():
            user_data = df[df['user_id'] == user_id]
            
            profile = {
                'basic_stats': {
                    'total_entries': len(user_data),
                    'date_range': {
                        'start': user_data['date'].min().isoformat(),
                        'end': user_data['date'].max().isoformat(),
                        'days_active': (user_data['date'].max() - user_data['date'].min()).days + 1
                    },
                    'avg_mood': float(user_data['mood_score'].mean()),
                    'mood_stability': float(user_data['mood_score'].std()),
                    'mood_range': {
                        'min': float(user_data['mood_score'].min()),
                        'max': float(user_data['mood_score'].max())
                    }
                },
                'patterns': {
                    'weekend_effect': self._calculate_weekend_effect(user_data),
                    'sleep_correlation': self._calculate_sleep_mood_correlation(user_data),
                    'stress_impact': self._calculate_stress_impact(user_data),
                    'exercise_benefit': self._calculate_exercise_benefit(user_data)
                },
                'behavioral_indicators': {
                    'consistency': self._calculate_tracking_consistency(user_data),
                    'engagement': self._calculate_engagement_score(user_data),
                    'risk_factors': self._identify_risk_factors(user_data)
                },
                'recommendations': self._generate_user_recommendations(user_data)
            }
            
            user_profiles[str(user_id)] = profile
        
        return user_profiles
    
    def _calculate_weekend_effect(self, user_data: pd.DataFrame) -> Dict:
        """Calculate weekend vs weekday mood differences."""
        if 'is_weekend' in user_data.columns:
            weekend_mood = user_data[user_data['is_weekend'] == 1]['mood_score'].mean()
            weekday_mood = user_data[user_data['is_weekend'] == 0]['mood_score'].mean()
            
            return {
                'weekend_avg': float(weekend_mood) if not pd.isna(weekend_mood) else None,
                'weekday_avg': float(weekday_mood) if not pd.isna(weekday_mood) else None,
                'difference': float(weekend_mood - weekday_mood) if not pd.isna(weekend_mood - weekday_mood) else None
            }
        return {}
    
    def _calculate_sleep_mood_correlation(self, user_data: pd.DataFrame) -> Dict:
        """Calculate correlation between sleep and mood."""
        if 'sleep_hours' in user_data.columns and len(user_data) > 3:
            correlation = user_data['sleep_hours'].corr(user_data['mood_score'])
            
            return {
                'correlation': float(correlation) if not pd.isna(correlation) else None,
                'strength': 'strong' if abs(correlation) > 0.7 else 'moderate' if abs(correlation) > 0.3 else 'weak',
                'optimal_sleep': float(user_data[user_data['mood_score'] >= 4.0]['sleep_hours'].median()) if len(user_data[user_data['mood_score'] >= 4.0]) > 0 else None
            }
        return {}
    
    def _calculate_stress_impact(self, user_data: pd.DataFrame) -> Dict:
        """Calculate how stress affects mood."""
        if 'stress_level' in user_data.columns and len(user_data) > 3:
            correlation = user_data['stress_level'].corr(user_data['mood_score'])
            
            high_stress_data = user_data[user_data['stress_level'] >= 7]
            low_stress_data = user_data[user_data['stress_level'] <= 3]
            
            return {
                'correlation': float(correlation) if not pd.isna(correlation) else None,
                'high_stress_avg_mood': float(high_stress_data['mood_score'].mean()) if len(high_stress_data) > 0 else None,
                'low_stress_avg_mood': float(low_stress_data['mood_score'].mean()) if len(low_stress_data) > 0 else None,
                'stress_sensitivity': 'high' if abs(correlation) > 0.6 else 'moderate' if abs(correlation) > 0.3 else 'low'
            }
        return {}
    
    def _calculate_exercise_benefit(self, user_data: pd.DataFrame) -> Dict:
        """Calculate exercise impact on mood."""
        if 'exercise_minutes' in user_data.columns and len(user_data) > 3:
            correlation = user_data['exercise_minutes'].corr(user_data['mood_score'])
            
            exercise_days = user_data[user_data['exercise_minutes'] > 20]
            no_exercise_days = user_data[user_data['exercise_minutes'] == 0]
            
            return {
                'correlation': float(correlation) if not pd.isna(correlation) else None,
                'exercise_day_mood': float(exercise_days['mood_score'].mean()) if len(exercise_days) > 0 else None,
                'no_exercise_mood': float(no_exercise_days['mood_score'].mean()) if len(no_exercise_days) > 0 else None,
                'exercise_frequency': len(exercise_days) / len(user_data)
            }
        return {}
    
    def _calculate_tracking_consistency(self, user_data: pd.DataFrame) -> Dict:
        """Calculate how consistently user tracks mood."""
        date_range = (user_data['date'].max() - user_data['date'].min()).days + 1
        entries_count = len(user_data)
        consistency_rate = entries_count / date_range if date_range > 0 else 0
        
        return {
            'rate': float(consistency_rate),
            'category': 'high' if consistency_rate > 0.8 else 'medium' if consistency_rate > 0.5 else 'low',
            'total_days': int(date_range),
            'tracked_days': int(entries_count)
        }
    
    def _calculate_engagement_score(self, user_data: pd.DataFrame) -> Dict:
        """Calculate user engagement with the app."""
        engagement_factors = []
        
        # Note length engagement
        if 'notes' in user_data.columns:
            avg_note_length = user_data['notes'].fillna('').str.len().mean()
            engagement_factors.append(min(avg_note_length / 50, 1.0))  # Normalize to 0-1
        
        # Games played
        if 'games_played' in user_data.columns:
            avg_games = user_data['games_played'].mean()
            engagement_factors.append(min(avg_games / 3, 1.0))  # Normalize to 0-1
        
        # Breathing exercises
        if 'breathing_minutes' in user_data.columns:
            avg_breathing = user_data['breathing_minutes'].mean()
            engagement_factors.append(min(avg_breathing / 20, 1.0))  # Normalize to 0-1
        
        overall_engagement = np.mean(engagement_factors) if engagement_factors else 0.5
        
        return {
            'score': float(overall_engagement),
            'level': 'high' if overall_engagement > 0.7 else 'medium' if overall_engagement > 0.4 else 'low',
            'factors': engagement_factors
        }
    
    def _identify_risk_factors(self, user_data: pd.DataFrame) -> List[str]:
        """Identify potential risk factors for the user."""
        risk_factors = []
        
        # Low mood trend
        if user_data['mood_score'].mean() < 2.5:
            risk_factors.append('chronically_low_mood')
        
        # High mood volatility
        if user_data['mood_score'].std() > 1.5:
            risk_factors.append('high_mood_volatility')
        
        # Sleep issues
        if 'sleep_hours' in user_data.columns:
            avg_sleep = user_data['sleep_hours'].mean()
            if avg_sleep < 6.0:
                risk_factors.append('chronic_sleep_deprivation')
            elif user_data['sleep_hours'].std() > 2.0:
                risk_factors.append('irregular_sleep_pattern')
        
        # High stress
        if 'stress_level' in user_data.columns and user_data['stress_level'].mean() > 6:
            risk_factors.append('chronic_high_stress')
        
        # Social isolation
        if 'social_interaction' in user_data.columns and user_data['social_interaction'].mean() < 1:
            risk_factors.append('social_isolation')
        
        # Sedentary lifestyle
        if 'exercise_minutes' in user_data.columns and user_data['exercise_minutes'].mean() < 15:
            risk_factors.append('sedentary_lifestyle')
        
        return risk_factors
    
    def _generate_user_recommendations(self, user_data: pd.DataFrame) -> List[str]:
        """Generate personalized recommendations for the user."""
        recommendations = []
        
        # Sleep recommendations
        if 'sleep_hours' in user_data.columns:
            avg_sleep = user_data['sleep_hours'].mean()
            if avg_sleep < 7:
                recommendations.append('Focus on improving sleep duration - aim for 7-9 hours nightly')
            
            sleep_mood_corr = user_data['sleep_hours'].corr(user_data['mood_score'])
            if sleep_mood_corr > 0.5:
                recommendations.append('Your mood strongly correlates with sleep - prioritize sleep hygiene')
        
        # Exercise recommendations
        if 'exercise_minutes' in user_data.columns:
            avg_exercise = user_data['exercise_minutes'].mean()
            if avg_exercise < 30:
                recommendations.append('Increase physical activity - even 20 minutes daily can improve mood')
        
        # Stress management
        if 'stress_level' in user_data.columns and user_data['stress_level'].mean() > 5:
            recommendations.append('Practice stress management techniques like breathing exercises')
        
        # Social connection
        if 'social_interaction' in user_data.columns and user_data['social_interaction'].mean() < 2:
            recommendations.append('Increase social connections - reach out to friends or join activities')
        
        # Consistency
        consistency = self._calculate_tracking_consistency(user_data)
        if consistency['rate'] < 0.7:
            recommendations.append('Track your mood more consistently for better insights')
        
        return recommendations


def load_and_preprocess_data(file_path: str) -> Tuple[pd.DataFrame, Dict]:
    """Convenience function to load and preprocess data from CSV."""
    try:
        df = pd.read_csv(file_path)
        preprocessor = DataPreprocessor()
        processed_df, report = preprocessor.preprocess(df)
        return processed_df, report
    except Exception as e:
        logger.error(f"Error loading and preprocessing data: {str(e)}")
        raise


if __name__ == "__main__":
    # Example usage
    sample_data = {
        'user_id': ['user_001'] * 5,
        'date': ['2024-01-15', '2024-01-16', '2024-01-17', '2024-01-18', '2024-01-19'],
        'mood_score': [4.2, 3.8, 4.5, 3.2, 4.8],
        'sleep_hours': [7.5, 6.0, 8.0, 5.5, 9.0],
        'stress_level': [3, 4, 2, 5, 1],
        'exercise_minutes': [30, 0, 45, 0, 60],
        'notes': ['Good morning run', 'Tired day', 'Great dinner with friends', 'Stressful deadline', 'Perfect day']
    }
    
    df = pd.DataFrame(sample_data)
    
    preprocessor = DataPreprocessor()
    processed_df, report = preprocessor.preprocess(df)
    
    print("Preprocessing Report:")
    print(json.dumps(report, indent=2))
    print(f"\nProcessed data shape: {processed_df.shape}")
    print(f"Columns: {list(processed_df.columns)}")
